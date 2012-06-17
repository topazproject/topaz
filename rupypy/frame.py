from pypy.rlib import jit

from rupypy.objects.cellobject import W_CellObject


class BaseFrame(object):
    def __init__(self):
        self.backref = jit.vref_None
        self.escaped = False


class Frame(BaseFrame):
    _virtualizable2_ = [
        "bytecode", "locals_w[*]", "stack_w[*]", "stackpos", "w_self",
        "w_scope", "block", "cells[*]", "lastblock",
    ]

    @jit.unroll_safe
    def __init__(self, bytecode, w_self, w_scope, block, parent_interp):
        self = jit.hint(self, fresh_virtualizable=True, access_directly=True)
        BaseFrame.__init__(self)
        self.bytecode = bytecode
        self.stack_w = [None] * bytecode.max_stackdepth
        self.locals_w = [None] * len(bytecode.locals)
        self.cells = [W_CellObject() for _ in bytecode.cellvars] + [None] * len(bytecode.freevars)
        self.stackpos = 0
        self.w_self = w_self
        self.w_scope = w_scope
        self.block = block
        self.parent_interp = parent_interp
        self.lastblock = None

    def _set_normal_arg(self, bytecode, i, w_value):
        loc = bytecode.arg_locs[i]
        pos = bytecode.arg_pos[i]
        self._set_arg(bytecode, loc, pos, w_value)

    def _set_arg(self, bytecode, loc, pos, w_value):
        assert pos >= 0
        if loc == bytecode.LOCAL:
            self.locals_w[pos] = w_value
        elif loc == bytecode.CELL:
            self.cells[pos].set(w_value)

    @jit.unroll_safe
    def handle_args(self, space, bytecode, args_w, block):
        from rupypy.interpreter import Interpreter

        assert len(args_w) >= (len(bytecode.arg_locs) - len(bytecode.defaults))
        assert bytecode.splat_arg_pos != -1 or 0 <= len(bytecode.arg_locs) - len(args_w)

        ec = space.getexecutioncontext()

        for i in xrange(min(len(args_w), len(bytecode.arg_locs))):
            self._set_normal_arg(bytecode, i, args_w[i])
        defl_start = len(args_w) - (len(bytecode.arg_locs) - len(bytecode.defaults))
        for i in xrange(len(bytecode.arg_locs) - len(args_w)):
            bc = bytecode.defaults[i + defl_start]
            w_value = Interpreter().interpret(space, self, bc)
            self._set_normal_arg(bytecode, i + len(args_w), w_value)

        if bytecode.splat_arg_pos != -1:
            splat_args_w = args_w[len(bytecode.arg_locs):]
            w_splat_args = ec.space.newarray(splat_args_w)
            self._set_arg(bytecode, bytecode.splat_arg_loc, bytecode.splat_arg_pos, w_splat_args)

        if bytecode.block_arg_pos != -1:
            if block is None:
                w_block = ec.space.w_nil
            else:
                w_block = ec.space.newproc(block)
            self._set_arg(bytecode, bytecode.block_arg_loc, bytecode.block_arg_pos, w_block)

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

    @jit.unroll_safe
    def popitemsreverse(self, n):
        items_w = [None] * n
        for i in xrange(n - 1, -1, -1):
            items_w[i] = self.pop()
        return items_w

    def peek(self):
        stackpos = jit.promote(self.stackpos) - 1
        assert stackpos >= 0
        return self.stack_w[stackpos]

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

    def get_filename(self):
        return self.bytecode.filepath

    def get_lineno(self, idx):
        return self.bytecode.lineno_table[idx]

    def get_code_name(self):
        return self.bytecode.name


class BuiltinFrame(BaseFrame):
    def __init__(self, name):
        BaseFrame.__init__(self)
        self.name = name

    def get_filename(self):
        return self.backref().get_filename()

    def get_lineno(self, idx):
        return self.backref().get_lineno(idx)

    def get_code_name(self):
        return self.name
