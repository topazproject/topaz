from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_BaseObject


class W_TrueObject(W_BaseObject):
    classdef = ClassDef("TrueClass")

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr("true")
        
    def bool_w(self, space):
        return True

class W_FalseObject(W_BaseObject):
    classdef = ClassDef("FalseClass")

    def is_true(self, space):
        return False

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr("false")

    def bool_w(self, space):
        return False