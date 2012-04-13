from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_BaseObject


class W_NilObject(W_BaseObject):
    classdef = ClassDef("NilClass", W_BaseObject.classdef)

    def is_true(self, space):
        return False

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr("")
