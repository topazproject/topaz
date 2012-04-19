class Bytecode(object):
    _immutable_fields_ = ["code", "consts[*]", "max_stackdepth", "locals[*]"]

    def __init__(self, code, max_stackdepth, consts, locals):
        self.code = code
        self.max_stackdepth = max_stackdepth
        self.consts_w = consts
        self.locals = locals