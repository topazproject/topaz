from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object


class W_NilObject(W_Object):
    classdef = ClassDef("NilClass", W_Object.classdef)

    def is_true(self, space):
        return False

    @classdef.method("inspect")
    def method_inspect(self, space):
        return space.newstr_fromstr("nil")

    @classdef.method("nil?")
    def method_nil(self, space):
        return space.newbool(True)

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr("")

    @classdef.method("to_a")
    def method_to_a(self, space):
        return space.newarray([])

    @classdef.method("to_f")
    def method_to_f(self, space):
        return space.newfloat(0.0)

    @classdef.method("to_i")
    def method_to_a(self, space):
        return space.newint(0)
