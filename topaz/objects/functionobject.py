import copy

from topaz.objects.objectobject import W_BaseObject


class W_FunctionObject(W_BaseObject):
    _immutable_fields_ = ["name", "w_class", "visibility?"]

    PUBLIC = 0
    PROTECTED = 1
    PRIVATE = 2
    MODULE_FUNCTION = 3

    def __init__(self, name, w_class=None, visibility=PUBLIC):
        self.name = name
        self.w_class = w_class
        self.visibility = visibility

    def __deepcopy__(self, memo):
        obj = super(W_FunctionObject, self).__deepcopy__(memo)
        obj.name = self.name
        obj.w_class = copy.deepcopy(self.w_class, memo)
        obj.visibility = copy.deepcopy(self.visibility, memo)
        return obj

    def update_visibility(self, visibility):
        self.visibility = visibility

    def arity(self, space):
        return space.newint(0)

    def source_location(self, space):
        return space.w_nil


class W_UserFunction(W_FunctionObject):
    _immutable_fields_ = ["bytecode", "lexical_scope"]

    def __init__(self, name, bytecode, lexical_scope, visibility=W_FunctionObject.PUBLIC):
        W_FunctionObject.__init__(self, name, visibility=visibility)
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

    def arity(self, space):
        return space.newint(self.bytecode.arity(negative_defaults=True))

    def source_location(self, space):
        return space.newarray([
            space.newstr_fromstr(self.bytecode.filepath),
            space.newint(self.bytecode.lineno)
        ])


class W_BuiltinFunction(W_FunctionObject):
    _immutable_fields_ = ["func"]

    def __init__(self, name, w_class, func, visibility=W_FunctionObject.PUBLIC):
        W_FunctionObject.__init__(self, name, w_class, visibility=visibility)
        self.func = func

    def __deepcopy__(self, memo):
        obj = super(W_BuiltinFunction, self).__deepcopy__(memo)
        obj.func = self.func
        return obj

    def call(self, space, w_receiver, args_w, block):
        from topaz.frame import BuiltinFrame

        frame = BuiltinFrame(self.name)
        ec = space.getexecutioncontext()
        ec.invoke_trace_proc(space, "c-call", self.name, self.w_class.name)
        with ec.visit_frame(frame):
            w_res = self.func(w_receiver, space, args_w, block)
        ec.invoke_trace_proc(space, "c-return", self.name, self.w_class.name)
        return w_res
