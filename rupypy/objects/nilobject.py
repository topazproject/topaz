from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object, W_BuiltinObject

class W_NilObject(W_BuiltinObject):
    classdef = ClassDef("NilClass", W_Object.classdef)

    def is_true(self, space):
        return False

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr("")
