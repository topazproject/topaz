import copy

from pypy.rlib import jit

from rupypy.frame import BuiltinFrame
from rupypy.objects.objectobject import W_BaseObject


class W_FunctionObject(W_BaseObject):
    pass


class W_UserFunction(W_FunctionObject):
    _immutable_fields_ = ["bytecode", "lexical_scope"]

    def __init__(self, name, bytecode, lexical_scope):
        self.name = name
        self.bytecode = bytecode
        self.lexical_scope = lexical_scope

    def __deepcopy__(self, memo):
        obj = super(W_UserFunction, self).__deepcopy__(memo)
        obj.name = self.name
        obj.bytecode = copy.deepcopy(self.bytecode, memo)
        obj.lexical_scope = copy.deepcopy(self.lexical_scope, memo)
        return obj

    @jit.unroll_safe
    def call(self, space, w_receiver, args_w, block):
        frame = space.create_frame(
            self.bytecode,
            w_self=w_receiver,
            w_scope=space.getscope(w_receiver),
            lexical_scope=self.lexical_scope,
            block=block,
        )
        with space.getexecutioncontext().visit_frame(frame):
            frame.handle_args(space, self.bytecode, args_w, block)
            return space.execute_frame(frame, self.bytecode)


class W_BuiltinFunction(W_FunctionObject):
    _immutable_fields_ = ["name", "func"]

    def __init__(self, name, func):
        self.name = name
        self.func = func

    def __deepcopy__(self, memo):
        obj = super(W_BuiltinFunction, self).__deepcopy__(memo)
        obj.name = self.name
        obj.func = self.func
        return obj

    def call(self, space, w_receiver, args_w, block):
        frame = BuiltinFrame(self.name)
        with space.getexecutioncontext().visit_frame(frame):
            return self.func(w_receiver, space, args_w, block)
