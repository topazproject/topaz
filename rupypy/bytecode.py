from rupypy import consts


class CompilerContext(object):
    def __init__(self, space):
        self.space = space
        self.data = []
        self.consts = []

    def create_bytecode(self):
        bc = "".join(self.data)
        return Bytecode(bc, self.count_stackdepth(bc), self.consts)

    def count_stackdepth(self, bc):
        i = 0
        current_stackdepth = max_stackdepth = 0
        while i < len(bc):
            c = ord(bc[i])
            i += 1
            stack_effect = consts.BYTECODE_STACK_EFFECT[c]
            if stack_effect == consts.SEND_EFFECT:
                stack_effect = -ord(bc[i+1])
            i += consts.BYTECODE_NUM_ARGS[c]
            current_stackdepth += stack_effect
            max_stackdepth = max(max_stackdepth, current_stackdepth)
        return max_stackdepth

    def emit(self, c, *args):
        assert len(args) == consts.BYTECODE_NUM_ARGS[c]
        self.data.append(chr(c))
        for arg in args:
            self.data.append(chr(arg))

    def create_const(self, w_obj):
        i = len(self.consts)
        self.consts.append(w_obj)
        return i

    def create_int_const(self, intvalue):
        return self.create_const(self.space.newint(intvalue))

    def create_symbol_const(self, symbol):
        return self.create_const(self.space.newsymbol(symbol))


class Bytecode(object):
    def __init__(self, code, max_stackdepth, consts):
        self.code = code
        self.max_stackdepth = max_stackdepth
        self.consts = consts