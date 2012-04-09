from pypy.rlib.objectmodel import we_are_translated, specialize
from pypy.rlib.unroll import unrolling_iterable

from rupypy import consts


class Frame(object):
    def __init__(self, bytecode, w_self):
        self.stack = [None] * bytecode.max_stackdepth
        self.locals_w = [None] * len(bytecode.locals)
        self.stackpos = 0
        self.w_self = w_self

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
            if instr == consts.RETURN:
                assert frame.stackpos == 1
                return frame.pop()

            if we_are_translated():
                for i, name in consts.UNROLLING_BYTECODES:
                    if i == instr:
                        pc = self.run_instr(space, i, name, bytecode, frame, pc)
                        break
                else:
                    raise NotImplementedError
            else:
                pc = self.run_instr(space, instr, consts.BYTECODE_NAMES[instr], bytecode, frame, pc)

    @specialize.arg(2, 3)
    def run_instr(self, space, instr, name, bytecode, frame, pc):
        args = ()
        for i in unrolling_xrange(consts.BYTECODE_NUM_ARGS[instr]):
            args += (ord(bytecode.code[pc]),)
            pc += 1

        method = getattr(self, name)
        res = method(space, bytecode, frame, pc, *args)
        if res is not None:
            pc = res
        return pc

    def LOAD_CONST(self, space, bytecode, frame, pc, idx):
        frame.push(bytecode.consts[idx])

    def LOAD_SELF(self, space, bytecode, frame, pc):
        frame.push(frame.w_self)

    def SEND(self, space, bytecode, frame, pc, meth_idx, num_args):
        args_w = [frame.pop() for _ in range(num_args)]
        w_receiver = frame.pop()
        w_res = space.send(w_receiver, bytecode.consts[meth_idx], args_w)
        frame.push(w_res)

    def DISCARD_TOP(self, space, bytecode, frame, pc):
        frame.pop()


@specialize.memo()
def unrolling_xrange(n):
    return unrolling_iterable(xrange(n))