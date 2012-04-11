from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object


class W_NilObject(W_Object):
    classdef = ClassDef("NilClass", W_Object.classdef)

    def is_true(self, space):
        return False

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr([])
