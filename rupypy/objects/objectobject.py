from rupypy.module import ClassDef, finalize
from rupypy.modules.kernel import Kernel


@finalize
class W_Object(object):
    _attrs_ = ()

    classdef = ClassDef("Object")
    classdef.include_module(Kernel)

    def getclass(self, space):
        return space.getclassobject(self.classdef)