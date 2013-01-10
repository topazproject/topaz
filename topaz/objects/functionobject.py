import copy

from topaz.frame import BuiltinFrame
from topaz.objects.objectobject import W_BaseObject


class W_FunctionObject(W_BaseObject):
    _immutable_fields_ = ["name"]

    def __init__(self, name, w_class=None):
        self.name = name
        self.w_class = w_class

    def __deepcopy__(self, memo):
        obj = super(W_FunctionObject, self).__deepcopy__(memo)
        obj.name = self.name
        obj.w_class = copy.deepcopy(self.w_class, memo)
        return obj


class W_UserFunction(W_FunctionObject):
    _immutable_fields_ = ["bytecode", "lexical_scope"]

    def __init__(self, name, bytecode, lexical_scope):
        W_FunctionObject.__init__(self, name)
        self.bytecode = bytecode
        self.lexical_scope = lexical_scope

    def __deepcopy__(self, memo):
        obj = super(W_UserFunction, self).__deepcopy__(memo)
        obj.bytecode = copy.deepcopy(self.bytecode, memo)
        obj.lexical_scope = copy.deepcopy(self.lexical_scope, memo)
        return obj

    def call(self, space, w_receiver, args_w, block):
        frame = space.create_frame(
            self.bytecode,
            w_self=w_receiver,
            lexical_scope=self.lexical_scope,
            block=block,
        )
        with space.getexecutioncontext().visit_frame(frame):
            frame.handle_args(space, self.bytecode, args_w, block)
            return space.execute_frame(frame, self.bytecode)


class W_BuiltinFunction(W_FunctionObject):
    _immutable_fields_ = ["func"]

    def __init__(self, name, w_class, func):
        W_FunctionObject.__init__(self, name, w_class)
        self.func = func

    def __deepcopy__(self, memo):
        obj = super(W_BuiltinFunction, self).__deepcopy__(memo)
        obj.func = self.func
        return obj

    def call(self, space, w_receiver, args_w, block):
        frame = BuiltinFrame(self.name)
        ec = space.getexecutioncontext()
        ec.invoke_trace_proc(space, "c-call", self.name, self.w_class.name)
        with ec.visit_frame(frame):
            w_res = self.func(w_receiver, space, args_w, block)
        ec.invoke_trace_proc(space, "c-return", self.name, self.w_class.name)
        return w_res
