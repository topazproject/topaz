from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object


class W_FiberObject(W_Object):
    classdef = ClassDef("Fiber", W_Object.classdef, filepath=__file__)

    def __init__(self, space, klass):
        W_Object.__init__(self, space, klass)
        self.w_block = None

    @classdef.singleton_method("allocate")
    def singleton_method_allocate(self, space):
        return W_FiberObject(space, self)

    @classdef.method("initialize")
    def method_initialize(self, space, block):
        if block is None:
            raise space.error(space.w_ArgumentError)
        self.w_block = block

    @classdef.method("resume")
    def method_resume(self, space, args_w):
        pass
