from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object


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
