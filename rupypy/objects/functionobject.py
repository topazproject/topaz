from pypy.rlib import jit

from rupypy.objects.objectobject import W_BaseObject


class W_FunctionObject(W_BaseObject):
    pass


class W_UserFunction(W_FunctionObject):
    _immutable_fields_ = ["bytecode"]

    def __init__(self, name, bytecode):
        self.name = name
        self.bytecode = bytecode

    @jit.unroll_safe
    def call(self, space, w_receiver, args_w, block):
        from rupypy.interpreter import Interpreter

        frame = space.create_frame(
            self.bytecode,
            w_self=w_receiver,
            w_scope=space.getclass(w_receiver),
            block=block,
        )
        frame.handle_args(space, self.bytecode, args_w, block)
        return Interpreter().interpret(space, frame, self.bytecode)


class W_BuiltinFunction(W_FunctionObject):
    _immutable_fields_ = ["func"]

    def __init__(self, func):
        self.func = func

    def call(self, space, w_receiver, args_w, block):
        return self.func(w_receiver, space, args_w, block)
