from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object


class W_ProcObject(W_Object):
    classdef = ClassDef("Proc", W_Object.classdef, filepath=__file__)

    def __init__(self, space, block, is_lambda):
        W_Object.__init__(self, space)
        self.block = block
        self.is_lambda = is_lambda

    @classdef.method("[]")
    @classdef.method("call")
    def method_call(self, space, args_w):
        from topaz.interpreter import RaiseReturn, RaiseBreak

        try:
            return space.invoke_block(self.block, args_w)
        except RaiseReturn as e:
            if self.is_lambda:
                return e.w_value
            else:
                raise
        except RaiseBreak as e:
            if self.is_lambda:
                return e.w_value
            else:
                raise space.error(space.w_LocalJumpError, "break from proc-closure")

    @classdef.method("lambda?")
    def method_lambda(self, space):
        return space.newbool(self.is_lambda)

    @classdef.singleton_method("allocate")
    def method_allocate(self, space, args_w, block):
        return W_ProcObject(space, block, False)
