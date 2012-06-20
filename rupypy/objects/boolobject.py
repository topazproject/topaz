from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object


class W_TrueObject(W_Object):
    classdef = ClassDef("TrueClass", W_Object.classdef)

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr("true")

class W_FalseObject(W_Object):
    classdef = ClassDef("FalseClass", W_Object.classdef)

    def is_true(self, space):
        return False

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr("false")
