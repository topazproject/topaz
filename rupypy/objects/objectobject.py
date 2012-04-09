from rupypy.module import ClassDef
from rupypy.modules.kernel import Kernel


class W_Object(object):
    classdef = ClassDef("Object")

    classdef.include_module(Kernel)

    def getclass(self, space):
        return space.getclassobject(self.classdef)