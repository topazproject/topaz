class Bytecode(object):
    _immutable_fields_ = [
        "code", "consts_w[*]", "max_stackdepth", "locals[*]", "cells[*]"
    ]

    def __init__(self, code, max_stackdepth, consts, locals, cells):
        self.code = code
        self.max_stackdepth = max_stackdepth
        self.consts_w = consts
        self.locals = locals
        self.cells = cells
