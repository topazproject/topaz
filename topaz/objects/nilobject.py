from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object


class W_NilObject(W_Object):
    classdef = ClassDef("NilClass", W_Object.classdef)

    def is_true(self, space):
        return False

    def getsingletonclass(self, space):
        return space.getclassfor(W_NilObject)

    @classdef.method("nil?")
    def method_nilp(self, space):
        return space.w_true

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr("")

    @classdef.method("inspect")
    def method_inspect(self, space):
        return space.newstr_fromstr("nil")

    @classdef.method("to_i")
    def method_to_i(self, space):
        return space.newint(0)

    @classdef.method("to_f")
    def method_to_f(self, space):
        return space.newfloat(0.0)

    @classdef.method("to_a")
    def method_to_a(self, space):
        return space.newarray([])

    @classdef.method("&")
    def method_and(self, space, w_other):
        return space.w_false

    @classdef.method("|")
    @classdef.method("^")
    def method_or(self, space, w_other):
        return space.newbool(space.is_true(w_other))
