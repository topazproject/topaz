from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_BaseObject


class W_ProcObject(W_BaseObject):
    classdef = ClassDef("Proc", W_BaseObject.classdef)

    def __init__(self, block):
        self.block = block

    @classdef.method("call")
    def method_call(self, space, args_w):
        return space.invoke_block(self.block, args_w)