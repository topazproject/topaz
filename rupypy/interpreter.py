from rupypy import consts


class Frame(object):
    def __init__(self, bytecode):
        self.stack = [None] * bytecode.max_stackdepth
        self.locals_w = [None] * len(bytecode.locals)
        self.stackpos = 0

    def push(self, w_obj):
        self.stack[self.stackpos] = w_obj
        self.stackpos += 1

    def pop(self):
        stackpos = self.stackpos - 1
        assert self.stackpos >= 0
        w_res = self.stack[stackpos]
        self.stack[stackpos] = None
        self.stackpos = stackpos
        return w_res

class Interpreter(object):
    def interpret(self, space, frame, bytecode):
        pc = 0
        while True:
            instr = ord(bytecode.code[pc])
            pc += 1
            args = ()
            for i in xrange(consts.BYTECODE_NUM_ARGS[instr]):
                args += (ord(bytecode.code[pc]),)
                pc += 1

            if instr == consts.RETURN:
                assert frame.stackpos == 1
                return frame.pop()

            method = getattr(self, consts.BYTECODE_NAMES[instr])
            res = method(space, bytecode, frame, pc, *args)
            if res is not None:
                pc = res

    def LOAD_CONST(self, space, bytecode, frame, pc, idx):
        frame.push(bytecode.consts[idx])

    def SEND(self, space, bytecode, frame, pc, meth_idx, num_args):
        args_w = [frame.pop() for _ in range(num_args)]
        w_receiver = frame.pop()
        w_res = space.send(w_receiver, bytecode.consts[meth_idx], args_w)
        frame.push(w_res)

    def DISCARD_TOP(self, space, bytecode, frame, pc):
        frame.pop()
