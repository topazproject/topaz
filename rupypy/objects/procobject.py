from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_BaseObject


class W_ProcObject(W_BaseObject):
    classdef = ClassDef("Proc", W_BaseObject.classdef)

    def __init__(self, block):
        self.block = block

    @classdef.method("call")
    def method_call(self, ec, args_w):
        return ec.space.invoke_block(ec, self.block, args_w)
