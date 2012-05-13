from pypy.rlib import jit

from rupypy.frame import BuiltinFrame
from rupypy.objects.objectobject import W_BaseObject


class W_FunctionObject(W_BaseObject):
    pass


class W_UserFunction(W_FunctionObject):
    _immutable_fields_ = ["bytecode"]

    def __init__(self, name, bytecode):
        self.name = name
        self.bytecode = bytecode

    @jit.unroll_safe
    def call(self, ec, w_receiver, args_w, block):
        frame = ec.space.create_frame(
            self.bytecode,
            w_self=w_receiver,
            w_scope=ec.space.getclass(w_receiver),
            block=block,
        )
        with ec.visit_frame(frame):
            frame.handle_args(ec, self.bytecode, args_w, block)
            return ec.space.execute_frame(ec, frame, self.bytecode)


class W_BuiltinFunction(W_FunctionObject):
    _immutable_fields_ = ["name", "func"]

    def __init__(self, name, func):
        self.name = name
        self.func = func

    def call(self, ec, w_receiver, args_w, block):
        frame = BuiltinFrame(self.name)
        with ec.visit_frame(frame, append_instr=True):
            return self.func(w_receiver, ec, args_w, block)
