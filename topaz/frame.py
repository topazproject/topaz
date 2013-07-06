from rpython.rlib import jit

from topaz.closure import LocalCell
from topaz.objects.arrayobject import W_ArrayObject
from topaz.objects.functionobject import W_FunctionObject


class BaseFrame(object):
    _attrs_ = ["backref", "escaped", "back_last_instr"]

    def __init__(self):
        self.backref = jit.vref_None
        self.escaped = False


class Frame(BaseFrame):
    _virtualizable2_ = [
        "bytecode", "localsstack_w[*]", "stackpos", "w_self", "block",
        "cells[*]", "lastblock", "lexical_scope", "last_instr", "parent_interp",
        "top_parent_interp",
    ]

    @jit.unroll_safe
    def __init__(self, bytecode, w_self, lexical_scope, block, parent_interp,
                 top_parent_interp, regexp_match_cell):
        self = jit.hint(self, fresh_virtualizable=True, access_directly=True)
        BaseFrame.__init__(self)
        self.bytecode = bytecode
        self.localsstack_w = [None] * (len(bytecode.cellvars) + bytecode.max_stackdepth)
        self.stackpos = len(bytecode.cellvars)
        self.last_instr = 0
        self.cells = [LocalCell() for _ in bytecode.cellvars] + [None] * len(bytecode.freevars)
        self.regexp_match_cell = regexp_match_cell
        self.w_self = w_self
        self.lexical_scope = lexical_scope
        self.block = block
        self.parent_interp = parent_interp
        self.top_parent_interp = top_parent_interp
        self.visibility = W_FunctionObject.PUBLIC
        self.lastblock = None

    def _set_arg(self, space, pos, w_value):
        assert pos >= 0
        self.cells[pos].set(space, self, pos, w_value)

    def handle_block_args(self, space, bytecode, args_w, block):
        if (len(args_w) == 1 and
            isinstance(args_w[0], W_ArrayObject) and len(bytecode.arg_pos) >= 2):
            w_arg = args_w[0]
            args_w = space.listview(w_arg)
        minargc = len(bytecode.arg_pos) - len(bytecode.defaults)
        if len(args_w) < minargc:
            args_w.extend([space.w_nil] * (minargc - len(args_w)))
        if bytecode.splat_arg_pos == -1:
            if len(args_w) > len(bytecode.arg_pos):
                del args_w[len(bytecode.arg_pos):]
        return self.handle_args(space, bytecode, args_w, block)

    @jit.unroll_safe
    def handle_args(self, space, bytecode, args_w, block):
        from topaz.interpreter import Interpreter

        if (len(args_w) < (len(bytecode.arg_pos) - len(bytecode.defaults)) or
            (bytecode.splat_arg_pos == -1 and len(args_w) > len(bytecode.arg_pos))):
            raise space.error(space.w_ArgumentError,
                "wrong number of arguments (%d for %d)" % (len(args_w), len(bytecode.arg_pos) - len(bytecode.defaults))
            )

        for i in xrange(min(len(args_w), len(bytecode.arg_pos))):
            self._set_arg(space, bytecode.arg_pos[i], args_w[i])
        defl_start = len(args_w) - (len(bytecode.arg_pos) - len(bytecode.defaults))
        for i in xrange(len(bytecode.arg_pos) - len(args_w)):
            bc = bytecode.defaults[i + defl_start]
            self.bytecode = bc
            w_value = Interpreter().interpret(space, self, bc)
            self._set_arg(space, bytecode.arg_pos[i + len(args_w)], w_value)
        self.bytecode = bytecode

        if bytecode.splat_arg_pos != -1:
            if len(bytecode.arg_pos) > len(args_w):
                splat_args_w = []
            else:
                splat_args_w = args_w[len(bytecode.arg_pos):]
            w_splat_args = space.newarray(splat_args_w)
            self._set_arg(space, bytecode.splat_arg_pos, w_splat_args)

        if bytecode.block_arg_pos != -1:
            if block is None:
                w_block = space.w_nil
            else:
                w_block = block.copy(space)
            self._set_arg(space, bytecode.block_arg_pos, w_block)

    def push(self, w_obj):
        stackpos = jit.promote(self.stackpos)
        self.localsstack_w[stackpos] = w_obj
        self.stackpos = stackpos + 1

    def pop(self):
        stackpos = jit.promote(self.stackpos) - 1
        assert stackpos >= 0
        w_res = self.localsstack_w[stackpos]
        self.localsstack_w[stackpos] = None
        self.stackpos = stackpos
        return w_res

    @jit.unroll_safe
    def popitemsreverse(self, n):
        items_w = [None] * n
        for i in xrange(n - 1, -1, -1):
            items_w[i] = self.pop()
        return items_w

    def peek(self):
        stackpos = jit.promote(self.stackpos) - 1
        assert stackpos >= 0
        return self.localsstack_w[stackpos]

    def popblock(self):
        lastblock = self.lastblock
        if lastblock is not None:
            self.lastblock = lastblock.lastblock
        return lastblock

    @jit.unroll_safe
    def unrollstack(self, kind):
        while self.lastblock is not None:
            block = self.popblock()
            if block.handling_mask & kind:
                return block
            block.cleanupstack(self)

    def unrollstack_and_jump(self, space, unroller):
        block = self.unrollstack(unroller.kind)
        return block.handle(space, self, unroller)

    def has_contents(self):
        return True

    def get_filename(self):
        return self.bytecode.filepath

    def get_lineno(self, prev_frame):
        if prev_frame is None:
            instr = self.last_instr
        else:
            instr = prev_frame.back_last_instr - 1
        return self.bytecode.lineno_table[instr]

    def get_code_name(self):
        return self.bytecode.name


class BuiltinFrame(BaseFrame):
    def __init__(self, name):
        BaseFrame.__init__(self)
        self.name = name

    def has_contents(self):
        return self.backref() is not None

    def get_filename(self):
        return self.backref().get_filename()

    def get_lineno(self, prev_frame):
        return self.backref().get_lineno(self)

    def get_code_name(self):
        return self.name
