from pypy.rlib import jit
from pypy.rlib.objectmodel import we_are_translated, specialize

from rupypy import consts
from rupypy.objects.cellobject import W_CellObject


class Frame(object):
    _virtualizable2_ = [
        "locals_w[*]", "stack_w[*]", "stackpos", "w_self", "w_scope", "block",
        "cells[*]"
    ]

    @jit.unroll_safe
    def __init__(self, bytecode, w_self, w_scope, block):
        self = jit.hint(self, fresh_virtualizable=True, access_directly=True)
        self.stack_w = [None] * bytecode.max_stackdepth
        self.locals_w = [None] * len(bytecode.locals)
        self.cells = [W_CellObject() for _ in bytecode.cells]
        self.stackpos = 0
        self.w_self = w_self
        self.w_scope = w_scope
        self.block = block

    @jit.unroll_safe
    def handle_args(self, bytecode, args_w):
        assert len(args_w) == len(bytecode.arg_locs)
        for i in xrange(len(args_w)):
            loc = bytecode.arg_locs[i]
            pos = bytecode.arg_pos[i]
            assert pos >= 0
            if loc == bytecode.LOCAL:
                self.locals_w[pos] = args_w[i]
            elif loc == bytecode.CELL:
                self.cells[pos].set(args_w[i])

    def push(self, w_obj):
        stackpos = jit.promote(self.stackpos)
        self.stack_w[stackpos] = w_obj
        self.stackpos = stackpos + 1

    def pop(self):
        stackpos = jit.promote(self.stackpos) - 1
        assert stackpos >= 0
        w_res = self.stack_w[stackpos]
        self.stack_w[stackpos] = None
        self.stackpos = stackpos
        return w_res

    def peek(self):
        stackpos = jit.promote(self.stackpos) - 1
        assert stackpos >= 0
        return self.stack_w[stackpos]

def get_printable_location(pc, bytecode):
    return consts.BYTECODE_NAMES[ord(bytecode.code[pc])]

class Interpreter(object):
    jitdriver = jit.JitDriver(
        greens = ["pc", "bytecode"],
        reds = ["self", "frame"],
        virtualizables = ["frame"],
        get_printable_location=get_printable_location,
    )

    def interpret(self, space, frame, bytecode):
        pc = 0
        while True:
            self.jitdriver.jit_merge_point(
                self=self, bytecode=bytecode, frame=frame, pc=pc
            )
            instr = ord(bytecode.code[pc])
            pc += 1
            if instr == consts.RETURN:
                assert frame.stackpos == 1
                return frame.pop()

            if we_are_translated():
                for i, name in consts.UNROLLING_BYTECODES:
                    if i == instr:
                        pc = self.run_instr(space, name, consts.BYTECODE_NUM_ARGS[i], bytecode, frame, pc)
                        break
                else:
                    raise NotImplementedError
            else:
                pc = self.run_instr(space, consts.BYTECODE_NAMES[instr], consts.BYTECODE_NUM_ARGS[instr], bytecode, frame, pc)

    @specialize.arg(2, 3)
    def run_instr(self, space, name, num_args, bytecode, frame, pc):
        args = ()
        if num_args >= 1:
            args += (ord(bytecode.code[pc]),)
            pc += 1
        if num_args >= 2:
            args += (ord(bytecode.code[pc]),)
            pc += 1
        if num_args >= 3:
            raise NotImplementedError

        method = getattr(self, name)
        res = method(space, bytecode, frame, pc, *args)
        if res is not None:
            pc = res
        return pc

    def jump(self, bytecode, frame, cur_pc, target_pc):
        if target_pc < cur_pc:
            self.jitdriver.can_enter_jit(
                self=self, bytecode=bytecode, frame=frame, pc=target_pc,
            )
        return target_pc

    def LOAD_SELF(self, space, bytecode, frame, pc):
        w_self = frame.w_self
        jit.promote(space.getclass(w_self))
        frame.push(w_self)

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

    def LOAD_CONSTANT(self, space, bytecode, frame, pc, idx):
        w_name = bytecode.consts_w[idx]
        name = space.symbol_w(w_name)
        w_obj = space.find_const(frame.w_scope, name)
        frame.push(w_obj)

    def STORE_CONSTANT(self, space, bytecode, frame, pc, idx):
        w_name = bytecode.consts_w[idx]
        name = space.symbol_w(w_name)
        w_obj = frame.pop()
        space.set_const(frame.w_scope, name, w_obj)
        frame.push(w_obj)

    def LOAD_INSTANCE_VAR(self, space, bytecode, frame, pc, idx):
        w_name = bytecode.consts_w[idx]
        w_obj = frame.pop()
        w_res = space.find_instance_var(w_obj, space.symbol_w(w_name))
        frame.push(w_res)

    def STORE_INSTANCE_VAR(self, space, bytecode, frame, pc, idx):
        w_name = bytecode.consts_w[idx]
        w_obj = frame.pop()
        w_value = frame.peek()
        space.set_instance_var(w_obj, space.symbol_w(w_name), w_value)

    @jit.unroll_safe
    def BUILD_ARRAY(self, space, bytecode, frame, pc, n_items):
        items_w = [None] * n_items
        for i in xrange(n_items - 1, -1, -1):
            items_w[i] = frame.pop()
        frame.push(space.newarray(items_w))

    def BUILD_RANGE(self, space, bytecode, frame, pc):
        w_end = frame.pop()
        w_start = frame.pop()
        w_range = space.newrange(w_start, w_end, False)
        frame.push(w_range)

    def BUILD_RANGE_INCLUSIVE(self, space, bytecode, frame, pc):
        w_end = frame.pop()
        w_start = frame.pop()
        w_range = space.newrange(w_start, w_end, True)
        frame.push(w_range)

    @jit.unroll_safe
    def BUILD_BLOCK(self, space, bytecode, frame, pc, n_cells):
        from rupypy.objects.blockobject import W_BlockObject
        from rupypy.objects.codeobject import W_CodeObject

        cells = [frame.pop() for _ in range(n_cells)]
        w_code = frame.pop()
        assert isinstance(w_code, W_CodeObject)
        block = W_BlockObject(w_code.bytecode, frame.w_self, cells, frame.block)
        frame.push(block)

    def BUILD_CLASS(self, space, bytecode, frame, pc):
        from rupypy.objects.codeobject import W_CodeObject
        from rupypy.objects.objectobject import W_Object

        w_bytecode = frame.pop()
        superclass = frame.pop()
        w_name = frame.pop()
        w_self = frame.pop()

        name = space.symbol_w(w_name)
        w_cls = space.find_const(frame.w_scope, name)
        if w_cls is None:
            if superclass is space.w_nil:
                superclass = space.getclassfor(W_Object)
            w_cls = space.newclass(name, superclass)
            space.set_const(frame.w_scope, name, w_cls)

        assert isinstance(w_bytecode, W_CodeObject)
        sub_frame = space.create_frame(w_bytecode.bytecode, w_cls, w_cls)
        Interpreter().interpret(space, sub_frame, w_bytecode.bytecode)

        frame.push(space.w_nil)

    def COPY_STRING(self, space, bytecode, frame, pc):
        from rupypy.objects.stringobject import W_StringObject

        w_s = frame.pop()
        assert isinstance(w_s, W_StringObject)
        frame.push(w_s.copy())

    def DEFINE_FUNCTION(self, space, bytecode, frame, pc):
        w_code = frame.pop()
        w_name = frame.pop()
        w_self = frame.pop()
        func = space.newfunction(w_name, w_code)
        w_self.add_method(space, space.symbol_w(w_name), func)
        frame.push(space.w_nil)

    @jit.unroll_safe
    def SEND(self, space, bytecode, frame, pc, meth_idx, num_args):
        args_w = [frame.pop() for _ in range(num_args)]
        w_receiver = frame.pop()
        w_res = space.send(w_receiver, bytecode.consts_w[meth_idx], args_w)
        frame.push(w_res)

    def SEND_BLOCK(self, space, bytecode, frame, pc, meth_idx, num_args):
        from rupypy.objects.blockobject import W_BlockObject

        w_block = frame.pop()
        args_w = [frame.pop() for _ in range(num_args - 1)]
        w_receiver = frame.pop()
        assert isinstance(w_block, W_BlockObject)
        w_res = space.send(w_receiver, bytecode.consts_w[meth_idx], args_w, block=w_block)
        frame.push(w_res)

    def JUMP(self, space, bytecode, frame, pc, target_pc):
        return self.jump(bytecode, frame, pc, target_pc)

    def JUMP_IF_FALSE(self, space, bytecode, frame, pc, target_pc):
        if space.is_true(frame.pop()):
            return pc
        else:
            return self.jump(bytecode, frame, pc, target_pc)

    def DISCARD_TOP(self, space, bytecode, frame, pc):
        frame.pop()

    def DUP_TOP(self, space, bytecode, frame, pc):
        frame.push(frame.peek())

    @jit.unroll_safe
    def YIELD(self, space, bytecode, frame, pc, n_args):
        args_w = [None] * n_args
        for i in xrange(n_args -1, -1, -1):
            args_w[i] = frame.pop()
        w_res = space.invoke_block(frame.block, args_w)
        frame.push(w_res)

    def UNREACHABLE(self, space, bytecode, frame, pc):
        raise Exception
    # Handled specially in the main dispatch loop.
    RETURN = UNREACHABLE
