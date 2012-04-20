class Bytecode(object):
    _immutable_fields_ = [
        "code", "consts_w[*]", "max_stackdepth", "locals[*]", "cells[*]", "arg_locs[*]"
    ]

    UNKNOWN = 0
    LOCAL = 1
    CELL = 2

    def __init__(self, code, max_stackdepth, consts, args, locals, cells):
        self.code = code
        self.max_stackdepth = max_stackdepth
        self.consts_w = consts
        self.locals = locals
        self.cells = cells

        arg_locs = [self.UNKNOWN] * len(args)
        for idx, arg in enumerate(args):
            if arg in locals:
                arg_locs[idx] = self.LOCAL
            elif arg in cells:
                arg_locs[idx] = self.CELL
        self.arg_locs = arg_locs
