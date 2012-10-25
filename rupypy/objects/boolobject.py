from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object


class W_TrueObject(W_Object):
    classdef = ClassDef("TrueClass", W_Object.classdef)

    @classdef.method("inspect")
    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr("true")

    @classdef.method("==")
    def method_eq(self, space, w_other):
        return space.newbool(self is w_other)

    @classdef.method("^")
    def method_xor(self, space, w_other):
        return space.newbool(not space.is_true(w_other))


class W_FalseObject(W_Object):
    classdef = ClassDef("FalseClass", W_Object.classdef)

    def is_true(self, space):
        return False

    @classdef.method("inspect")
    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr("false")

    @classdef.method("==")
    def method_eq(self, space, w_other):
        return space.newbool(self is w_other)

    @classdef.method("^")
    def method_xor(self, space, w_other):
        return space.newbool(space.is_true(w_other))
