from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_BaseObject


class W_ProcObject(W_BaseObject):
    classdef = ClassDef("Proc", W_BaseObject.classdef)

    def __init__(self, block, is_lambda):
        self.block = block
        self.is_lambda = is_lambda

    @classdef.method("call")
    def method_call(self, space, args_w):
        return space.invoke_block(self.block, args_w)

    @classdef.method("lambda?")
    def method_lambda(self, space):
        return space.newbool(self.is_lambda)
