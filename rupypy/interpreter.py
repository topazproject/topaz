from pypy.rlib import jit
from pypy.rlib.debug import check_nonneg
from pypy.rlib.objectmodel import we_are_translated, specialize, newlist_hint

from rupypy import consts
from rupypy.error import RubyError
from rupypy.objects.objectobject import W_BaseObject
from rupypy.objects.exceptionobject import W_TypeError, W_NameError
from rupypy.objects.functionobject import W_FunctionObject
from rupypy.objects.procobject import W_ProcObject
from rupypy.objects.stringobject import W_StringObject


def get_printable_location(pc, bytecode):
    return consts.BYTECODE_NAMES[ord(bytecode.code[pc])]


class Interpreter(object):
    jitdriver = jit.JitDriver(
        greens=["pc", "bytecode"],
        reds=["self", "ec", "frame"],
        virtualizables=["frame"],
        get_printable_location=get_printable_location,
    )

    def interpret(self, ec, frame, bytecode):
        pc = 0
        try:
            while True:
                self.jitdriver.jit_merge_point(
                    self=self, ec=ec, bytecode=bytecode, frame=frame, pc=pc
                )
                try:
                    pc = self.handle_bytecode(ec, pc, frame, bytecode)
                except RubyError as e:
                    pc = self.handle_ruby_error(ec, pc, frame, bytecode, e)
        except RaiseReturn as e:
            if e.parent_interp is self:
                return e.w_value
            raise
        except Return as e:
            return e.w_value

    def handle_bytecode(self, ec, pc, frame, bytecode):
        instr = ord(bytecode.code[pc])
        pc += 1
        if we_are_translated():
            for i, name in consts.UNROLLING_BYTECODES:
                if i == instr:
                    pc = self.run_instr(ec, name, consts.BYTECODE_NUM_ARGS[i], bytecode, frame, pc)
                    break
            else:
                raise NotImplementedError
        else:
            pc = self.run_instr(ec, consts.BYTECODE_NAMES[instr], consts.BYTECODE_NUM_ARGS[instr], bytecode, frame, pc)
        return pc

    @specialize.arg(2, 3)
    def run_instr(self, ec, name, num_args, bytecode, frame, pc):
        args = ()
        # Do not change these from * 256 to << 8, lshift has defined overflow
        # semantics which cause it to not propogate the nonnegative-ness.
        if num_args >= 1:
            v = ord(bytecode.code[pc]) | (ord(bytecode.code[pc + 1]) * 256)
            check_nonneg(v)
            args += (v,)
            pc += 2
        if num_args >= 2:
            v = ord(bytecode.code[pc]) | (ord(bytecode.code[pc + 1]) * 256)
            check_nonneg(v)
            args += (v,)
            pc += 2
        if num_args >= 3:
            raise NotImplementedError

        method = getattr(self, name)
        res = method(ec, bytecode, frame, pc, *args)
        if res is not None:
            pc = res
        return pc

    def handle_ruby_error(self, ec, pc, frame, bytecode, e):
        e.w_value.last_instructions.append(pc)
        block = frame.unrollstack(ApplicationException.kind)
        if block is None:
            raise
        unroller = ApplicationException(e)
        return block.handle(ec.space, frame, unroller)

    def jump(self, ec, bytecode, frame, cur_pc, target_pc):
        if target_pc < cur_pc:
            self.jitdriver.can_enter_jit(
                self=self, ec=ec, bytecode=bytecode, frame=frame, pc=target_pc,
            )
        return target_pc

    def LOAD_SELF(self, ec, bytecode, frame, pc):
        w_self = frame.w_self
        jit.promote(ec.space.getclass(w_self))
        frame.push(w_self)

    def LOAD_SCOPE(self, space, bytecode, frame, pc):
        frame.push(frame.w_scope)

    def LOAD_CODE(self, space, bytecode, frame, pc):
        frame.push(bytecode)

    def LOAD_CONST(self, space, bytecode, frame, pc, idx):
        frame.push(bytecode.consts_w[idx])

    def LOAD_LOCAL(self, space, bytecode, frame, pc, idx):
        frame.push(frame.locals_w[idx])

    def STORE_LOCAL(self, space, bytecode, frame, pc, idx):
        frame.locals_w[idx] = frame.peek()

    def LOAD_DEREF(self, space, bytecode, frame, pc, idx):
        frame.push(frame.cells[idx].get())

    def STORE_DEREF(self, space, bytecode, frame, pc, idx):
        frame.cells[idx].set(frame.peek())

    def LOAD_CLOSURE(self, space, bytecode, frame, pc, idx):
        frame.push(frame.cells[idx])

    def LOAD_CONSTANT(self, ec, bytecode, frame, pc, idx):
        w_scope = frame.pop()
        w_name = bytecode.consts_w[idx]
        name = ec.space.symbol_w(w_name)
        w_obj = ec.space.find_const(w_scope, name)
        if w_obj is None:
            ec.space.raise_(ec, ec.space.getclassfor(W_NameError),
                "uninitialized constant %s" % name
            )
        frame.push(w_obj)

    def STORE_CONSTANT(self, ec, bytecode, frame, pc, idx):
        w_name = bytecode.consts_w[idx]
        name = ec.space.symbol_w(w_name)
        w_value = frame.pop()
        w_scope = frame.pop()
        ec.space.set_const(w_scope, name, w_value)
        frame.push(w_value)

    def LOAD_INSTANCE_VAR(self, ec, bytecode, frame, pc, idx):
        w_name = bytecode.consts_w[idx]
        w_obj = frame.pop()
        w_res = ec.space.find_instance_var(w_obj, ec.space.symbol_w(w_name))
        frame.push(w_res)

    def STORE_INSTANCE_VAR(self, ec, bytecode, frame, pc, idx):
        w_name = bytecode.consts_w[idx]
        w_value = frame.pop()
        w_obj = frame.pop()
        ec.space.set_instance_var(w_obj, ec.space.symbol_w(w_name), w_value)
        frame.push(w_value)

    def LOAD_GLOBAL(self, ec, bytecode, frame, pc, idx):
        name = ec.space.symbol_w(bytecode.consts_w[idx])
        w_value = ec.space.globals.get(ec.space, name)
        frame.push(w_value)

    def STORE_GLOBAL(self, ec, bytecode, frame, pc, idx):
        name = ec.space.symbol_w(bytecode.consts_w[idx])
        w_value = frame.peek()
        ec.space.globals.set(ec.space, name, w_value)

    @jit.unroll_safe
    def BUILD_ARRAY(self, ec, bytecode, frame, pc, n_items):
        items_w = frame.popitemsreverse(n_items)
        frame.push(ec.space.newarray(items_w))

    @jit.unroll_safe
    def BUILD_STRING(self, ec, bytecode, frame, pc, n_items):
        items_w = frame.popitemsreverse(n_items)
        total_length = 0
        for w_item in items_w:
            assert isinstance(w_item, W_StringObject)
            total_length += w_item.length()

        storage = newlist_hint(total_length)
        for w_item in items_w:
            assert isinstance(w_item, W_StringObject)
            w_item.strategy.extend_into(w_item.storage, storage)
        frame.push(ec.space.newstr_fromchars(storage))

    def BUILD_HASH(self, ec, bytecode, frame, pc):
        frame.push(ec.space.newhash())

    def BUILD_RANGE(self, ec, bytecode, frame, pc):
        w_end = frame.pop()
        w_start = frame.pop()
        w_range = ec.space.newrange(w_start, w_end, False)
        frame.push(w_range)

    def BUILD_RANGE_INCLUSIVE(self, ec, bytecode, frame, pc):
        w_end = frame.pop()
        w_start = frame.pop()
        w_range = ec.space.newrange(w_start, w_end, True)
        frame.push(w_range)

    def BUILD_FUNCTION(self, ec, bytecode, frame, pc):
        w_code = frame.pop()
        w_name = frame.pop()
        w_func = ec.space.newfunction(w_name, w_code)
        frame.push(w_func)

    @jit.unroll_safe
    def BUILD_BLOCK(self, space, bytecode, frame, pc, n_cells):
        from rupypy.objects.blockobject import W_BlockObject
        from rupypy.objects.codeobject import W_CodeObject

        cells = [frame.pop() for _ in range(n_cells)]
        w_code = frame.pop()
        assert isinstance(w_code, W_CodeObject)
        block = W_BlockObject(
            w_code, frame.w_self, frame.w_scope, cells, frame.block, self
        )
        frame.push(block)

    def BUILD_CLASS(self, ec, bytecode, frame, pc):
        from rupypy.objects.objectobject import W_Object

        superclass = frame.pop()
        w_name = frame.pop()
        w_scope = frame.pop()

        name = ec.space.symbol_w(w_name)
        w_cls = ec.space.find_const(w_scope, name)
        if w_cls is None:
            if superclass is ec.space.w_nil:
                superclass = ec.space.getclassfor(W_Object)
            w_cls = ec.space.newclass(name, superclass)
            ec.space.set_const(w_scope, name, w_cls)

        frame.push(w_cls)

    def BUILD_MODULE(self, ec, bytecode, frame, pc):
        from rupypy.objects.codeobject import W_CodeObject

        w_bytecode = frame.pop()
        w_name = frame.pop()
        w_scope = frame.pop()

        name = ec.space.symbol_w(w_name)
        w_mod = ec.space.find_const(w_scope, name)
        if w_mod is None:
            w_mod = ec.space.newmodule(name)
            ec.space.set_const(w_scope, name, w_mod)

        assert isinstance(w_bytecode, W_CodeObject)
        sub_frame = ec.space.create_frame(w_bytecode, w_mod, w_mod)
        with ec.visit_frame(sub_frame):
            ec.space.execute_frame(ec, sub_frame, w_bytecode)

        frame.push(ec.space.w_nil)

    def BUILD_REGEXP(self, ec, bytecode, frame, pc):
        w_string = frame.pop()
        frame.push(ec.space.newregexp(ec.space.str_w(w_string)))

    def COPY_STRING(self, space, bytecode, frame, pc):
        from rupypy.objects.stringobject import W_StringObject

        w_s = frame.pop()
        assert isinstance(w_s, W_StringObject)
        frame.push(w_s.copy())

    def COERCE_ARRAY(self, ec, bytecode, frame, pc):
        from rupypy.objects.arrayobject import W_ArrayObject

        w_obj = frame.pop()
        if w_obj is ec.space.w_nil:
            frame.push(ec.space.newarray([]))
        elif isinstance(w_obj, W_ArrayObject):
            frame.push(w_obj)
        else:
            if ec.space.respond_to(w_obj, ec.space.newsymbol("to_a")):
                w_obj = ec.space.send(ec, w_obj, ec.space.newsymbol("to_a"))
            elif ec.space.respond_to(w_obj, ec.space.newsymbol("to_ary")):
                w_obj = ec.space.send(ec, w_obj, ec.space.newsymbol("to_ary"))
            if not isinstance(w_obj, W_ArrayObject):
                w_obj = ec.space.newarray([w_obj])
            frame.push(w_obj)

    def COERCE_BLOCK(self, ec, bytecode, frame, pc):
        w_block = frame.pop()
        if w_block is ec.space.w_nil:
            frame.push(w_block)
        elif isinstance(w_block, W_ProcObject):
            frame.push(w_block.block)
        else:
            ec.space.raise_(ec, ec.space.getclassfor(W_TypeError),
                "wrong argument type"
            )

    @jit.unroll_safe
    def UNPACK_SEQUENCE(self, ec, bytecode, frame, pc, n_items):
        w_obj = frame.pop()
        items_w = ec.space.listview(w_obj)
        for i in xrange(n_items - 1, -1, -1):
            try:
                w_obj = items_w[i]
            except IndexError:
                w_obj = ec.space.w_nil
            frame.push(w_obj)

    @jit.unroll_safe
    def UNPACK_SEQUENCE_FOR_SPLAT(self, ec, bytecode, frame, pc, n_targets, n_pre):
        w_obj = frame.pop()
        items_w = ec.space.listview(w_obj)
        n_items = len(items_w)
        n_post = n_targets - n_pre - 1
        n_splat = max(n_items - n_pre - n_post, 0)
        for i in xrange(n_items, n_pre + n_splat + n_post, 1):
            items_w.append(ec.space.w_nil)

        for i in xrange(n_pre + n_splat + n_post - 1, n_pre + n_splat - 1, -1):
            frame.push(items_w[i])
        splat_array = [items_w[i] for i in xrange(n_pre, n_pre + n_splat, 1)]
        frame.push(ec.space.newarray(splat_array))
        for i in xrange(n_pre - 1, -1, -1):
            frame.push(items_w[i])

    def DEFINE_FUNCTION(self, ec, bytecode, frame, pc):
        w_func = frame.pop()
        w_name = frame.pop()
        w_scope = frame.pop()
        assert isinstance(w_func, W_FunctionObject)
        w_scope.define_method(ec.space, ec.space.symbol_w(w_name), w_func)
        frame.push(ec.space.w_nil)

    def ATTACH_FUNCTION(self, ec, bytecode, frame, pc):
        w_func = frame.pop()
        w_name = frame.pop()
        w_obj = frame.pop()
        assert isinstance(w_func, W_FunctionObject)
        w_obj.attach_method(ec.space, ec.space.symbol_w(w_name), w_func)
        frame.push(ec.space.w_nil)

    def EVALUATE_CLASS(self, ec, bytecode, frame, pc):
        from rupypy.objects.codeobject import W_CodeObject

        w_bytecode = frame.pop()
        w_cls = frame.pop()
        assert isinstance(w_bytecode, W_CodeObject)
        sub_frame = ec.space.create_frame(w_bytecode, w_cls, w_cls)
        with ec.visit_frame(sub_frame):
            ec.space.execute_frame(ec, sub_frame, w_bytecode)

        frame.push(ec.space.w_nil)

    @jit.unroll_safe
    def SEND(self, ec, bytecode, frame, pc, meth_idx, num_args):
        args_w = frame.popitemsreverse(num_args)
        w_receiver = frame.pop()
        w_res = ec.space.send(ec, w_receiver, bytecode.consts_w[meth_idx], args_w)
        frame.push(w_res)

    @jit.unroll_safe
    def SEND_BLOCK(self, ec, bytecode, frame, pc, meth_idx, num_args):
        from rupypy.objects.blockobject import W_BlockObject

        w_block = frame.pop()
        args_w = frame.popitemsreverse(num_args - 1)
        w_receiver = frame.pop()
        if w_block is ec.space.w_nil:
            w_block = None
        else:
            assert isinstance(w_block, W_BlockObject)
        w_res = ec.space.send(ec, w_receiver, bytecode.consts_w[meth_idx], args_w, block=w_block)
        frame.push(w_res)

    def SEND_SPLAT(self, ec, bytecode, frame, pc, meth_idx):
        args_w = ec.space.listview(frame.pop())
        w_receiver = frame.pop()
        w_res = ec.space.send(ec, w_receiver, bytecode.consts_w[meth_idx], args_w)
        frame.push(w_res)

    def SEND_BLOCK_SPLAT(self, ec, bytecode, frame, pc, meth_idx):
        from rupypy.objects.blockobject import W_BlockObject

        w_block = frame.pop()
        args_w = ec.space.listview(frame.pop())
        w_receiver = frame.pop()
        assert isinstance(w_block, W_BlockObject)
        w_res = ec.space.send(ec, w_receiver, bytecode.consts_w[meth_idx], args_w, block=w_block)
        frame.push(w_res)

    def SETUP_EXCEPT(self, space, bytecode, frame, pc, target_pc):
        frame.lastblock = ExceptBlock(target_pc, frame.lastblock, frame.stackpos)

    def SETUP_FINALLY(self, space, bytecode, frame, pc, target_pc):
        frame.lastblock = FinallyBlock(target_pc, frame.lastblock, frame.stackpos)

    def END_FINALLY(self, ec, bytecode, frame, pc):
        frame.pop()
        unroller = frame.pop()
        if isinstance(unroller, SuspendedUnroller):
            block = frame.unrollstack(unroller.kind)
            if block is None:
                unroller.nomoreblocks()
            else:
                return block.handle(ec.space, frame, unroller)
        return pc

    def COMPARE_EXC(self, ec, bytecode, frame, pc):
        w_expected = frame.pop()
        w_actual = frame.peek()
        frame.push(ec.space.newbool(w_expected is ec.space.getclass(w_actual)))

    def POP_BLOCK(self, ec, bytecode, frame, pc):
        block = frame.popblock()
        block.cleanup(ec.space, frame)

    def JUMP(self, ec, bytecode, frame, pc, target_pc):
        return self.jump(ec, bytecode, frame, pc, target_pc)

    def JUMP_IF_TRUE(self, ec, bytecode, frame, pc, target_pc):
        if ec.space.is_true(frame.pop()):
            return self.jump(ec, bytecode, frame, pc, target_pc)
        else:
            return pc

    def JUMP_IF_FALSE(self, ec, bytecode, frame, pc, target_pc):
        if ec.space.is_true(frame.pop()):
            return pc
        else:
            return self.jump(ec, bytecode, frame, pc, target_pc)

    def UNARY_NOT(self, ec, bytecode, frame, pc):
        w_obj = frame.pop()
        frame.push(ec.space.newbool(not ec.space.is_true(w_obj)))

    def DISCARD_TOP(self, space, bytecode, frame, pc):
        frame.pop()

    def DUP_TOP(self, space, bytecode, frame, pc):
        frame.push(frame.peek())

    def DUP_TWO(self, space, bytecode, frame, pc):
        w_1 = frame.pop()
        w_2 = frame.pop()
        frame.push(w_2)
        frame.push(w_1)
        frame.push(w_2)
        frame.push(w_1)

    def ROT_TWO(self, space, bytecode, frame, pc):
        w_1 = frame.pop()
        w_2 = frame.pop()
        frame.push(w_1)
        frame.push(w_2)

    def ROT_THREE(self, space, bytecode, frame, pc):
        w_1 = frame.pop()
        w_2 = frame.pop()
        w_3 = frame.pop()
        frame.push(w_1)
        frame.push(w_3)
        frame.push(w_2)

    def RETURN(self, ec, bytecode, frame, pc):
        w_returnvalue = frame.pop()
        block = frame.unrollstack(ReturnValue.kind)
        if block is None:
            raise Return(w_returnvalue)
        unroller = ReturnValue(w_returnvalue)
        return block.handle(ec.space, frame, unroller)

    def RAISE_RETURN(self, ec, bytecode, frame, pc):
        w_returnvalue = frame.pop()
        block = frame.unrollstack(RaiseReturnValue.kind)
        if block is None:
            raise RaiseReturn(frame.parent_interp, w_returnvalue)
        unroller = RaiseReturnValue(frame.parent_interp, w_returnvalue)
        return block.handle(ec.space, frame, unroller)

    @jit.unroll_safe
    def YIELD(self, ec, bytecode, frame, pc, n_args):
        args_w = [None] * n_args
        for i in xrange(n_args - 1, -1, -1):
            args_w[i] = frame.pop()
        w_res = ec.space.invoke_block(ec, frame.block, args_w)
        frame.push(w_res)

    def UNREACHABLE(self, space, bytecode, frame, pc):
        raise Exception


class Return(Exception):
    def __init__(self, w_value):
        self.w_value = w_value


class RaiseReturn(Exception):
    def __init__(self, parent_interp, w_value):
        self.parent_interp = parent_interp
        self.w_value = w_value


class SuspendedUnroller(W_BaseObject):
    pass


class ApplicationException(SuspendedUnroller):
    kind = 1 << 1

    def __init__(self, e):
        self.e = e

    def nomoreblocks(self):
        raise self.e


class ReturnValue(SuspendedUnroller):
    kind = 1 << 2

    def __init__(self, w_returnvalue):
        self.w_returnvalue = w_returnvalue

    def nomoreblocks(self):
        raise Return(self.w_returnvalue)


class RaiseReturnValue(SuspendedUnroller):
    kind = 1 << 2

    def __init__(self, parent_interp, w_returnvalue):
        self.parent_interp = parent_interp
        self.w_returnvalue = w_returnvalue

    def nomoreblocks(self):
        raise RaiseReturn(self.parent_interp, self.w_returnvalue)


class FrameBlock(object):
    def __init__(self, target_pc, lastblock, stackdepth):
        self.target_pc = target_pc
        self.lastblock = lastblock
        # Leave one extra item on there, as the return value from this suite.
        self.stackdepth = stackdepth + 1

    @jit.unroll_safe
    def cleanupstack(self, frame):
        while frame.stackpos > self.stackdepth:
            frame.pop()


class ExceptBlock(FrameBlock):
    handling_mask = ApplicationException.kind

    def cleanup(self, space, frame):
        self.cleanupstack(frame)

    def handle(self, space, frame, unroller):
        self.cleanupstack(frame)
        e = unroller.e
        frame.push(unroller)
        frame.push(e.w_value)
        return self.target_pc


class FinallyBlock(FrameBlock):
    # Handles everything.
    handling_mask = -1

    def cleanup(self, space, frame):
        self.cleanupstack(frame)
        frame.push(space.w_nil)

    def handle(self, space, frame, unroller):
        self.cleanupstack(frame)
        frame.push(unroller)
        frame.push(space.w_nil)
        return self.target_pc
