from rpython.rlib import jit, rstackovf
from rpython.rlib.debug import check_nonneg
from rpython.rlib.objectmodel import we_are_translated, specialize

from topaz import consts
from topaz.error import RubyError
from topaz.objects.arrayobject import W_ArrayObject
from topaz.objects.classobject import W_ClassObject
from topaz.objects.codeobject import W_CodeObject
from topaz.objects.functionobject import W_FunctionObject
from topaz.objects.moduleobject import W_ModuleObject
from topaz.objects.objectobject import W_Root
from topaz.objects.procobject import W_ProcObject
from topaz.scope import StaticScope
from topaz.utils.regexp import RegexpError


def get_printable_location(pc, bytecode, block_bytecode, w_trace_proc):
    try:
        pcline = bytecode.lineno_table[pc]
    except IndexError:
        pcline = -1
    return "%s:%d(%d):in %s at %s" % (
        bytecode.filepath,
        bytecode.lineno,
        pcline,
        bytecode.name,
        consts.BYTECODE_NAMES[ord(bytecode.code[pc])]
    )


class Interpreter(object):
    jitdriver = jit.JitDriver(
        greens=["pc", "bytecode", "block_bytecode", "w_trace_proc"],
        reds=["self", "frame"],
        virtualizables=["frame"],
        get_printable_location=get_printable_location,
        check_untranslated=False,
        is_recursive=True
    )

    def __init__(self):
        self.finished = False

    def get_block_bytecode(self, block):
        return block.bytecode if block is not None else None

    def interpret(self, space, frame, bytecode, startpc=0):
        pc = startpc
        try:
            while True:
                self.jitdriver.jit_merge_point(
                    self=self, bytecode=bytecode, frame=frame, pc=pc,
                    block_bytecode=self.get_block_bytecode(frame.block),
                    w_trace_proc=space.getexecutioncontext().gettraceproc(),
                )
                pc = self._interpret(space, pc, frame, bytecode)
        except RaiseReturn as e:
            if e.parent_interp is self:
                return e.w_value
            raise
        except Return as e:
            return e.w_value
        finally:
            self.finished = True

    def _interpret(self, space, pc, frame, bytecode):
        prev_pc = frame.last_instr
        frame.last_instr = pc
        if (space.getexecutioncontext().hastraceproc() and
                bytecode.lineno_table[pc] != bytecode.lineno_table[prev_pc]):
            space.getexecutioncontext().invoke_trace_proc(
                space, "line", None, None, frame=frame)
        try:
            pc = self.handle_bytecode(space, pc, frame, bytecode)
        except RubyError as e:
            pc = self.handle_ruby_error(space, pc, frame, bytecode, e)
        except RaiseReturn as e:
            pc = self.handle_raise_return(space, pc, frame, bytecode, e)
        except RaiseBreak as e:
            pc = self.handle_raise_break(space, pc, frame, bytecode, e)
        except Throw as e:
            pc = self.handle_throw(space, pc, frame, bytecode, e)
        except rstackovf.StackOverflow:
            rstackovf.check_stack_overflow()
            pc = self.handle_ruby_error(
                space, pc, frame, bytecode,
                space.error(space.w_SystemStackError, "stack level too deep"))
        return pc

    def handle_bytecode(self, space, pc, frame, bytecode):
        instr = ord(bytecode.code[pc])
        pc += 1
        if we_are_translated():
            for i, name in consts.UNROLLING_BYTECODES:
                if i == instr:
                    pc = self.run_instr(
                        space, name, consts.BYTECODE_NUM_ARGS[i],
                        bytecode, frame, pc)
                    break
            else:
                raise SystemError
        else:
            pc = self.run_instr(
                space, consts.BYTECODE_NAMES[instr],
                consts.BYTECODE_NUM_ARGS[instr], bytecode, frame, pc)
        return pc

    @specialize.arg(2, 3)
    def run_instr(self, space, name, num_args, bytecode, frame, pc):
        args = ()
        # Do not change these from * 256 to << 8, lshift has defined overflow
        # semantics which cause it to not propagate the nonnegative-ness.
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
        try:
            res = method(space, bytecode, frame, pc, *args)
        except RaiseBreak as e:
            if e.parent_interp is not self:
                raise
            frame.push(e.w_value)
            res = None
        if res is not None:
            pc = res
        return pc

    def handle_ruby_error(self, space, pc, frame, bytecode, e):
        block = frame.unrollstack(ApplicationException.kind)
        if block is None:
            raise e
        unroller = ApplicationException(e)
        return block.handle(space, frame, unroller)

    def handle_raise_return(self, space, pc, frame, bytecode, e):
        block = frame.unrollstack(RaiseReturnValue.kind)
        if block is None:
            raise e
        unroller = RaiseReturnValue(e.parent_interp, e.w_value)
        return block.handle(space, frame, unroller)

    def handle_raise_break(self, space, pc, frame, bytecode, e):
        block = frame.unrollstack(RaiseBreakValue.kind)
        if block is None:
            raise e
        unroller = RaiseBreakValue(e.parent_interp, e.w_value)
        return block.handle(space, frame, unroller)

    def handle_throw(self, space, pc, frame, bytecode, e):
        block = frame.unrollstack(ThrowValue.kind)
        if block is None:
            raise e
        unroller = ThrowValue(e.name, e.w_value)
        return block.handle(space, frame, unroller)

    def jump(self, space, bytecode, frame, cur_pc, target_pc):
        if target_pc < cur_pc:
            self.jitdriver.can_enter_jit(
                self=self, bytecode=bytecode, frame=frame, pc=target_pc,
                block_bytecode=self.get_block_bytecode(frame.block),
                w_trace_proc=space.getexecutioncontext().gettraceproc()
            )
        return target_pc

    def LOAD_SELF(self, space, bytecode, frame, pc):
        w_self = frame.w_self
        jit.promote(space.getclass(w_self))
        frame.push(w_self)

    def LOAD_SCOPE(self, space, bytecode, frame, pc):
        if frame.lexical_scope is not None:
            frame.push(frame.lexical_scope.w_mod)
        else:
            frame.push(space.w_object)

    def LOAD_BLOCK(self, space, bytecode, frame, pc):
        frame.push(frame.block or space.w_nil)

    def LOAD_CODE(self, space, bytecode, frame, pc):
        frame.push(bytecode)

    def LOAD_CONST(self, space, bytecode, frame, pc, idx):
        frame.push(bytecode.consts_w[idx])

    def LOAD_DEREF(self, space, bytecode, frame, pc, idx):
        frame.push(frame.cells[idx].get(space, frame, idx) or space.w_nil)

    def STORE_DEREF(self, space, bytecode, frame, pc, idx):
        frame.cells[idx].set(space, frame, idx, frame.peek())

    def LOAD_CLOSURE(self, space, bytecode, frame, pc, idx):
        frame.push(frame.cells[idx].upgrade_to_closure(space, frame, idx))

    def LOAD_CONSTANT(self, space, bytecode, frame, pc, idx):
        space.getexecutioncontext().last_instr = pc
        w_scope = frame.pop()
        w_name = bytecode.consts_w[idx]
        name = space.symbol_w(w_name)
        w_obj = space.find_const(w_scope, name)
        frame.push(w_obj)

    def STORE_CONSTANT(self, space, bytecode, frame, pc, idx):
        space.getexecutioncontext().last_instr = pc
        w_name = bytecode.consts_w[idx]
        name = space.symbol_w(w_name)
        w_value = frame.pop()
        w_scope = frame.pop()
        space.set_const(w_scope, name, w_value)
        frame.push(w_value)

    def DEFINED_CONSTANT(self, space, bytecode, frame, pc, idx):
        space.getexecutioncontext().last_instr = pc
        w_name = bytecode.consts_w[idx]
        w_scope = frame.pop()
        if space.is_true(space.send(w_scope, "const_defined?", [w_name])):
            frame.push(space.newstr_fromstr("constant"))
        else:
            frame.push(space.w_nil)

    def LOAD_LOCAL_CONSTANT(self, space, bytecode, frame, pc, idx):
        space.getexecutioncontext().last_instr = pc
        frame.pop()
        w_name = bytecode.consts_w[idx]
        name = space.symbol_w(w_name)
        frame.push(space.find_lexical_const(
            jit.promote(frame.lexical_scope), name))

    @jit.unroll_safe
    def DEFINED_LOCAL_CONSTANT(self, space, bytecode, frame, pc, idx):
        space.getexecutioncontext().last_instr = pc
        frame.pop()
        w_name = bytecode.consts_w[idx]
        name = space.symbol_w(w_name)
        w_res = space._find_lexical_const(
            jit.promote(frame.lexical_scope), name, autoload=False)
        if w_res is None:
            frame.push(space.w_nil)
        else:
            frame.push(space.newstr_fromstr("constant"))

    def LOAD_INSTANCE_VAR(self, space, bytecode, frame, pc, idx):
        w_name = bytecode.consts_w[idx]
        w_obj = frame.pop()
        w_res = (space.find_instance_var(w_obj, space.symbol_w(w_name)) or
                 space.w_nil)
        frame.push(w_res)

    def STORE_INSTANCE_VAR(self, space, bytecode, frame, pc, idx):
        w_name = bytecode.consts_w[idx]
        w_value = frame.pop()
        w_obj = frame.pop()
        space.set_instance_var(w_obj, space.symbol_w(w_name), w_value)
        frame.push(w_value)

    def DEFINED_INSTANCE_VAR(self, space, bytecode, frame, pc, idx):
        space.getexecutioncontext().last_instr = pc
        w_name = bytecode.consts_w[idx]
        w_obj = frame.pop()
        if space.is_true(space.send(
                w_obj, "instance_variable_defined?", [w_name])):
            frame.push(space.newstr_fromstr("instance-variable"))
        else:
            frame.push(space.w_nil)

    def LOAD_CLASS_VAR(self, space, bytecode, frame, pc, idx):
        name = space.symbol_w(bytecode.consts_w[idx])
        w_module = frame.pop()
        assert isinstance(w_module, W_ModuleObject)
        w_value = space.find_class_var(w_module, name)
        frame.push(w_value)

    def STORE_CLASS_VAR(self, space, bytecode, frame, pc, idx):
        name = space.symbol_w(bytecode.consts_w[idx])
        w_value = frame.pop()
        w_module = frame.pop()
        assert isinstance(w_module, W_ModuleObject)
        space.set_class_var(w_module, name, w_value)
        frame.push(w_value)

    def DEFINED_CLASS_VAR(self, space, bytecode, frame, pc, idx):
        space.getexecutioncontext().last_instr = pc
        w_name = bytecode.consts_w[idx]
        w_obj = frame.pop()
        if space.is_true(space.send(
                w_obj, "class_variable_defined?", [w_name])):
            frame.push(space.newstr_fromstr("class variable"))
        else:
            frame.push(space.w_nil)

    def LOAD_GLOBAL(self, space, bytecode, frame, pc, idx):
        space.getexecutioncontext().last_instr = pc
        name = space.symbol_w(bytecode.consts_w[idx])
        w_value = space.globals.get(space, name) or space.w_nil
        frame.push(w_value)

    def STORE_GLOBAL(self, space, bytecode, frame, pc, idx):
        space.getexecutioncontext().last_instr = pc
        name = space.symbol_w(bytecode.consts_w[idx])
        w_value = frame.peek()
        space.globals.set(space, name, w_value)

    def DEFINED_GLOBAL(self, space, bytecode, frame, pc, idx):
        name = space.symbol_w(bytecode.consts_w[idx])
        if space.globals.get(space, name) is not None:
            frame.push(space.newstr_fromstr("global-variable"))
        else:
            frame.push(space.w_nil)

    def BUILD_ARRAY(self, space, bytecode, frame, pc, n_items):
        items_w = frame.popitemsreverse(n_items)
        frame.push(space.newarray(items_w))

    @jit.unroll_safe
    def BUILD_ARRAY_SPLAT(self, space, bytecode, frame, pc, n_items):
        arrays_w = frame.popitemsreverse(n_items)
        items_w = []
        for w_array in arrays_w:
            items_w.extend(space.listview(w_array))
        frame.push(space.newarray(items_w))

    def BUILD_STRING(self, space, bytecode, frame, pc, n_items):
        items_w = frame.popitemsreverse(n_items)
        frame.push(space.newstr_fromstrs(items_w))

    def BUILD_HASH(self, space, bytecode, frame, pc):
        frame.push(space.newhash())

    def BUILD_RANGE(self, space, bytecode, frame, pc):
        w_end = frame.pop()
        w_start = frame.pop()
        w_range = space.newrange(w_start, w_end, False)
        frame.push(w_range)

    def BUILD_RANGE_EXCLUSIVE(self, space, bytecode, frame, pc):
        w_end = frame.pop()
        w_start = frame.pop()
        w_range = space.newrange(w_start, w_end, True)
        frame.push(w_range)

    def BUILD_FUNCTION(self, space, bytecode, frame, pc):
        w_code = frame.pop()
        w_name = frame.pop()
        w_func = space.newfunction(
            w_name, w_code, frame.lexical_scope, frame.visibility)
        frame.push(w_func)

    @jit.unroll_safe
    def BUILD_BLOCK(self, space, bytecode, frame, pc, n_cells):
        cells = [frame.pop() for _ in range(n_cells)]
        w_code = frame.pop()
        assert isinstance(w_code, W_CodeObject)
        frame.push(space.newproc(
            w_code, frame.w_self, frame.lexical_scope, cells, frame.block,
            self, frame.top_parent_interp or self, frame.regexp_match_cell
        ))

    def BUILD_LAMBDA(self, space, bytecode, frame, pc):
        block = frame.pop()
        assert isinstance(block, W_ProcObject)
        frame.push(block.copy(space, is_lambda=True))

    def BUILD_CLASS(self, space, bytecode, frame, pc):
        space.getexecutioncontext().last_instr = pc
        superclass = frame.pop()
        w_name = frame.pop()
        w_scope = frame.pop()

        name = space.symbol_w(w_name)
        w_cls = w_scope.find_included_const(space, name, autoload=True)
        if w_cls is None:
            if superclass is space.w_nil:
                superclass = space.w_object
            if not space.is_kind_of(superclass, space.w_class):
                cls_name = space.obj_to_s(space.getclass(superclass))
                raise space.error(
                    space.w_TypeError,
                    "wrong argument type %s (expected Class)" % cls_name)
            assert isinstance(superclass, W_ClassObject)
            if superclass.is_singleton:
                raise space.error(
                    space.w_TypeError,
                    "can't make subclass of singleton class")
            w_cls = space.newclass(name, superclass, w_scope=w_scope)
            space.set_const(w_scope, name, w_cls)
        elif not space.is_kind_of(w_cls, space.w_class):
            raise space.error(space.w_TypeError, "%s is not a class" % name)
        else:
            assert isinstance(w_cls, W_ClassObject)
            if (superclass is not space.w_nil and
                    w_cls.superclass is not superclass):
                raise space.error(
                    space.w_TypeError,
                    "superclass mismatch for class %s" % w_cls.name)

        frame.push(w_cls)

    def BUILD_MODULE(self, space, bytecode, frame, pc):
        space.getexecutioncontext().last_instr = pc
        w_name = frame.pop()
        w_scope = frame.pop()

        name = space.symbol_w(w_name)
        w_mod = w_scope.find_included_const(space, name, autoload=True)

        if w_mod is None:
            w_mod = space.newmodule(name, w_scope=w_scope)
            space.set_const(w_scope, name, w_mod)
        elif (not space.is_kind_of(w_mod, space.w_module) or
                space.is_kind_of(w_mod, space.w_class)):
            raise space.error(space.w_TypeError, "%s is not a module" % name)

        frame.push(w_mod)

    def BUILD_REGEXP(self, space, bytecode, frame, pc):
        w_flags = frame.pop()
        w_string = frame.pop()
        try:
            w_regexp = space.newregexp(
                space.str_w(w_string), space.int_w(w_flags))
        except RegexpError as e:
            raise space.error(space.w_RegexpError, str(e))
        frame.push(w_regexp)

    def COERCE_ARRAY(self, space, bytecode, frame, pc, nil_is_empty):
        w_obj = frame.pop()
        if w_obj is space.w_nil:
            if nil_is_empty:
                frame.push(space.newarray([]))
            else:
                frame.push(space.newarray([space.w_nil]))
        elif isinstance(w_obj, W_ArrayObject):
            frame.push(w_obj)
        else:
            space.getexecutioncontext().last_instr = pc
            if space.respond_to(w_obj, "to_a"):
                w_res = space.send(w_obj, "to_a")
            elif space.respond_to(w_obj, "to_ary"):
                w_res = space.send(w_obj, "to_ary")
            else:
                w_res = space.newarray([w_obj])
            if not isinstance(w_res, W_ArrayObject):
                w_res = space.newarray([w_obj])
            frame.push(w_res)

    def COERCE_BLOCK(self, space, bytecode, frame, pc):
        w_block = frame.pop()
        if w_block is space.w_nil:
            frame.push(w_block)
        elif isinstance(w_block, W_ProcObject):
            frame.push(w_block)
        elif space.respond_to(w_block, "to_proc"):
            space.getexecutioncontext().last_instr = pc
            # Proc implements to_proc, too, but MRI doesn't call it
            w_res = space.convert_type(w_block, space.w_proc, "to_proc")
            assert isinstance(w_res, W_ProcObject)
            frame.push(w_res)
        else:
            raise space.error(space.w_TypeError, "wrong argument type")

    def COERCE_STRING(self, space, bytecode, frame, pc):
        w_symbol = frame.pop()
        frame.push(space.newstr_fromstr(space.symbol_w(w_symbol)))

    @jit.unroll_safe
    def UNPACK_SEQUENCE(self, space, bytecode, frame, pc, n_items):
        w_obj = frame.pop()
        items_w = space.listview(w_obj)
        for i in xrange(n_items - 1, -1, -1):
            try:
                w_obj = items_w[i]
            except IndexError:
                w_obj = space.w_nil
            frame.push(w_obj)

    @jit.unroll_safe
    def UNPACK_SEQUENCE_SPLAT(
            self, space, bytecode, frame, pc, n_targets, n_pre):
        w_obj = frame.pop()
        items_w = space.listview(w_obj)
        n_items = len(items_w)
        n_post = n_targets - n_pre - 1
        n_splat = max(n_items - n_pre - n_post, 0)
        for i in xrange(n_items, n_pre + n_splat + n_post, 1):
            items_w.append(space.w_nil)

        for i in xrange(n_pre + n_splat + n_post - 1, n_pre + n_splat - 1, -1):
            frame.push(items_w[i])
        splat_array = [items_w[i] for i in xrange(n_pre, n_pre + n_splat, 1)]
        frame.push(space.newarray(splat_array))
        for i in xrange(n_pre - 1, -1, -1):
            frame.push(items_w[i])

    def DEFINE_FUNCTION(self, space, bytecode, frame, pc):
        w_func = frame.pop()
        w_name = frame.pop()
        w_scope = frame.pop()
        assert isinstance(w_func, W_FunctionObject)
        # None is special case. It means that we are trying to define
        # a method on Symbol or Numeric.
        if w_scope is None:
            raise space.error(
                space.w_TypeError,
                """can't define singleton method "%s" for %s""" % (
                    space.symbol_w(w_name), space.getclass(frame.w_self).name))
        w_scope.define_method(space, space.symbol_w(w_name), w_func)
        frame.push(space.w_nil)

    def ATTACH_FUNCTION(self, space, bytecode, frame, pc):
        w_func = frame.pop()
        w_name = frame.pop()
        w_obj = frame.pop()
        if (space.is_kind_of(w_obj, space.w_symbol) or
                space.is_kind_of(w_obj, space.w_numeric)):
            raise space.error(
                space.w_TypeError, "no class/module to add method")
        assert isinstance(w_func, W_FunctionObject)
        w_obj.attach_method(space, space.symbol_w(w_name), w_func)
        frame.push(space.w_nil)

    def EVALUATE_MODULE(self, space, bytecode, frame, pc):
        space.getexecutioncontext().last_instr = pc
        w_bytecode = frame.pop()
        w_mod = frame.pop()
        assert isinstance(w_bytecode, W_CodeObject)

        event = "class" if space.is_kind_of(w_mod, space.w_class) else "module"
        space.getexecutioncontext().invoke_trace_proc(
            space, event, None, None, frame=frame)
        sub_frame = space.create_frame(
            w_bytecode, w_mod, StaticScope(w_mod, frame.lexical_scope),
            block=frame.block)
        with space.getexecutioncontext().visit_frame(sub_frame):
            w_res = space.execute_frame(sub_frame, w_bytecode)

        space.getexecutioncontext().invoke_trace_proc(
            space, "end", None, None, frame=frame)
        frame.push(w_res)

    def LOAD_SINGLETON_CLASS(self, space, bytecode, frame, pc):
        w_obj = frame.pop()
        if (space.is_kind_of(w_obj, space.w_symbol) or
                space.is_kind_of(w_obj, space.w_fixnum)):
            raise space.error(space.w_TypeError, "can't define singleton")
        frame.push(space.getsingletonclass(w_obj))

    def SEND(self, space, bytecode, frame, pc, meth_idx, num_args):
        space.getexecutioncontext().last_instr = pc
        args_w = frame.popitemsreverse(num_args)
        w_receiver = frame.pop()
        w_res = space.send(
            w_receiver, space.symbol_w(bytecode.consts_w[meth_idx]), args_w)
        frame.push(w_res)

    def SEND_BLOCK(self, space, bytecode, frame, pc, meth_idx, num_args):
        space.getexecutioncontext().last_instr = pc
        w_block = frame.pop()
        args_w = frame.popitemsreverse(num_args - 1)
        w_receiver = frame.pop()
        if w_block is space.w_nil:
            w_block = None
        else:
            assert isinstance(w_block, W_ProcObject)
        w_res = space.send(
            w_receiver, space.symbol_w(bytecode.consts_w[meth_idx]), args_w,
            block=w_block)
        frame.push(w_res)

    @jit.unroll_safe
    def SEND_SPLAT(self, space, bytecode, frame, pc, meth_idx, num_args):
        space.getexecutioncontext().last_instr = pc
        arrays_w = frame.popitemsreverse(num_args)
        length = 0
        for w_array in arrays_w:
            length += len(space.listview(w_array))
        args_w = [None] * length
        pos = 0
        for w_array in arrays_w:
            array_w = space.listview(w_array)
            args_w[pos:pos + len(array_w)] = array_w
            pos += len(array_w)
        w_receiver = frame.pop()
        w_res = space.send(
            w_receiver, space.symbol_w(bytecode.consts_w[meth_idx]), args_w)
        frame.push(w_res)

    @jit.unroll_safe
    def SEND_BLOCK_SPLAT(self, space, bytecode, frame, pc, meth_idx, num_args):
        space.getexecutioncontext().last_instr = pc
        w_block = frame.pop()
        arrays_w = frame.popitemsreverse(num_args - 1)
        args_w = []
        for w_array in arrays_w:
            args_w.extend(space.listview(w_array))
        w_receiver = frame.pop()
        if w_block is space.w_nil:
            w_block = None
        else:
            assert isinstance(w_block, W_ProcObject)
        w_res = space.send(
            w_receiver, space.symbol_w(bytecode.consts_w[meth_idx]), args_w,
            block=w_block)
        frame.push(w_res)

    def DEFINED_METHOD(self, space, bytecode, frame, pc, meth_idx):
        space.getexecutioncontext().last_instr = pc
        w_obj = frame.pop()
        if space.respond_to(
                w_obj, space.symbol_w(bytecode.consts_w[meth_idx])):
            frame.push(space.newstr_fromstr("method"))
        else:
            frame.push(space.w_nil)

    def SEND_SUPER_BLOCK(self, space, bytecode, frame, pc, meth_idx, num_args):
        space.getexecutioncontext().last_instr = pc
        w_block = frame.pop()
        args_w = frame.popitemsreverse(num_args - 1)
        w_receiver = frame.pop()
        if w_block is space.w_nil:
            w_block = None
        else:
            assert isinstance(w_block, W_ProcObject)
        if frame.lexical_scope is not None:
            w_cls = frame.lexical_scope.w_mod
        else:
            w_cls = space.getclass(w_receiver)
        w_res = space.send_super(
            w_cls, w_receiver, space.symbol_w(bytecode.consts_w[meth_idx]),
            args_w, block=w_block)
        frame.push(w_res)

    @jit.unroll_safe
    def SEND_SUPER_BLOCK_SPLAT(
            self, space, bytecode, frame, pc, meth_idx, num_args):
        space.getexecutioncontext().last_instr = pc
        w_block = frame.pop()
        arrays_w = frame.popitemsreverse(num_args - 1)
        args_w = []
        for w_array in arrays_w:
            args_w.extend(space.listview(w_array))
        w_receiver = frame.pop()
        if w_block is space.w_nil:
            w_block = None
        else:
            assert isinstance(w_block, W_ProcObject)
        if frame.lexical_scope is not None:
            w_cls = frame.lexical_scope.w_mod
        else:
            w_cls = space.getclass(w_receiver)
        w_res = space.send_super(
            w_cls, w_receiver, space.symbol_w(bytecode.consts_w[meth_idx]),
            args_w, block=w_block)
        frame.push(w_res)

    def DEFINED_SUPER(self, space, bytecode, frame, pc, meth_idx):
        space.getexecutioncontext().last_instr = pc
        w_obj = frame.pop()
        name = space.symbol_w(bytecode.consts_w[meth_idx])
        if space.getclass(w_obj).find_method_super(space, name) is not None:
            frame.push(space.newstr_fromstr("super"))
        else:
            frame.push(space.w_nil)

    def SETUP_LOOP(self, space, bytecode, frame, pc, target_pc):
        frame.lastblock = LoopBlock(target_pc, frame.lastblock, frame.stackpos)

    def SETUP_EXCEPT(self, space, bytecode, frame, pc, target_pc):
        frame.lastblock = ExceptBlock(
            target_pc, frame.lastblock, frame.stackpos)

    def SETUP_FINALLY(self, space, bytecode, frame, pc, target_pc):
        frame.lastblock = FinallyBlock(
            target_pc, frame.lastblock, frame.stackpos)

    def END_FINALLY(self, space, bytecode, frame, pc):
        frame.pop()
        unroller = frame.pop()
        if isinstance(unroller, SuspendedUnroller):
            block = frame.unrollstack(unroller.kind)
            if block is None:
                unroller.nomoreblocks()
            else:
                return block.handle(space, frame, unroller)
        return pc

    def POP_BLOCK(self, space, bytecode, frame, pc):
        block = frame.popblock()
        block.cleanup(space, frame)

    def JUMP(self, space, bytecode, frame, pc, target_pc):
        return self.jump(space, bytecode, frame, pc, target_pc)

    def JUMP_IF_TRUE(self, space, bytecode, frame, pc, target_pc):
        if space.is_true(frame.pop()):
            return self.jump(space, bytecode, frame, pc, target_pc)
        else:
            return pc

    def JUMP_IF_FALSE(self, space, bytecode, frame, pc, target_pc):
        if space.is_true(frame.pop()):
            return pc
        else:
            return self.jump(space, bytecode, frame, pc, target_pc)

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

    def RETURN(self, space, bytecode, frame, pc):
        w_returnvalue = frame.pop()
        block = frame.unrollstack(ReturnValue.kind)
        if block is None:
            raise Return(w_returnvalue)
        unroller = ReturnValue(w_returnvalue)
        return block.handle(space, frame, unroller)

    def RAISE_RETURN(self, space, bytecode, frame, pc):
        w_returnvalue = frame.pop()
        block = frame.unrollstack(RaiseReturnValue.kind)
        if block is None:
            raise RaiseReturn(frame.top_parent_interp, w_returnvalue)
        unroller = RaiseReturnValue(frame.top_parent_interp, w_returnvalue)
        return block.handle(space, frame, unroller)

    def YIELD(self, space, bytecode, frame, pc, n_args):
        if frame.block is None:
            raise space.error(space.w_LocalJumpError, "no block given (yield)")
        space.getexecutioncontext().last_instr = pc
        args_w = frame.popitemsreverse(n_args)
        w_res = space.invoke_block(frame.block, args_w)
        frame.push(w_res)

    @jit.unroll_safe
    def YIELD_SPLAT(self, space, bytecode, frame, pc, num_args):
        if frame.block is None:
            raise space.error(space.w_LocalJumpError, "no block given (yield)")
        space.getexecutioncontext().last_instr = pc
        arrays_w = frame.popitemsreverse(num_args)
        args_w = []
        for w_array in arrays_w:
            args_w.extend(space.listview(w_array))
        w_res = space.invoke_block(frame.block, args_w)
        frame.push(w_res)

    def DEFINED_YIELD(self, space, bytecode, frame, pc):
        if frame.block is not None:
            frame.push(space.newstr_fromstr("yield"))
        else:
            frame.push(space.w_nil)

    def CONTINUE_LOOP(self, space, bytecode, frame, pc, target_pc):
        frame.pop()
        return frame.unrollstack_and_jump(space, ContinueLoop(target_pc))

    def BREAK_LOOP(self, space, bytecode, frame, pc):
        w_obj = frame.pop()
        return frame.unrollstack_and_jump(space, BreakLoop(w_obj))

    def RAISE_BREAK(self, space, bytecode, frame, pc):
        if frame.parent_interp.finished:
            raise space.error(
                space.w_LocalJumpError, "break from proc-closure")
        w_value = frame.pop()
        block = frame.unrollstack(RaiseBreakValue.kind)
        if block is None:
            raise RaiseBreak(frame.parent_interp, w_value)
        unroller = RaiseBreakValue(frame.parent_interp, w_value)
        return block.handle(space, frame, unroller)


class Return(Exception):
    _immutable_fields_ = ["w_value"]

    def __init__(self, w_value):
        self.w_value = w_value


class RaiseFlow(Exception):
    def __init__(self, parent_interp, w_value):
        self.parent_interp = parent_interp
        self.w_value = w_value


class RaiseReturn(RaiseFlow):
    pass


class RaiseBreak(RaiseFlow):
    pass


class Throw(RaiseFlow):
    def __init__(self, name, w_value):
        self.name = name
        self.w_value = w_value


class SuspendedUnroller(W_Root):
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


class ContinueLoop(SuspendedUnroller):
    kind = 1 << 3

    def __init__(self, target_pc):
        self.target_pc = target_pc


class BreakLoop(SuspendedUnroller):
    kind = 1 << 4

    def __init__(self, w_value):
        self.w_value = w_value


class RaiseBreakValue(SuspendedUnroller):
    kind = 1 << 5

    def __init__(self, parent_interp, w_value):
        self.parent_interp = parent_interp
        self.w_value = w_value

    def nomoreblocks(self):
        raise RaiseBreak(self.parent_interp, self.w_value)


class ThrowValue(SuspendedUnroller):
    kind = 1 << 6

    def __init__(self, name, w_value):
        self.name = name
        self.w_value = w_value

    def nomoreblocks(self):
        raise Throw(self.name, self.w_value)


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


class LoopBlock(FrameBlock):
    handling_mask = ContinueLoop.kind | BreakLoop.kind

    def cleanup(self, space, frame):
        self.cleanupstack(frame)

    def handle(self, space, frame, unroller):
        if isinstance(unroller, ContinueLoop):
            frame.lastblock = self
            return unroller.target_pc
        elif isinstance(unroller, BreakLoop):
            self.cleanupstack(frame)
            frame.push(unroller.w_value)
            return self.target_pc
        else:
            raise SystemError


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
