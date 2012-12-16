from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object


class W_ProcObject(W_Object):
    classdef = ClassDef("Proc", W_Object.classdef, filepath=__file__)

    def __init__(self, space, block, is_lambda):
        W_Object.__init__(self, space)
        self.block = block
        self.is_lambda = is_lambda

    @classdef.method("[]")
    @classdef.method("call")
    def method_call(self, space, args_w):
        return space.invoke_block(self.block, args_w)

    @classdef.method("lambda?")
    def method_lambda(self, space):
        return space.newbool(self.is_lambda)

    @classdef.singleton_method("allocate")
    def method_allocate(self, space, args_w, block):
        return W_ProcObject(space, block, False)
