from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object


class W_NumericObject(W_Object):
    classdef = ClassDef("Numeric", W_Object.classdef)

    @classdef.method("<=>")
    def method_comparator(self, space, w_other):
        if self == w_other:
            return space.newint(0)
        else:
            return space.w_nil

    @classdef.method("to_int")
    def method_to_int(self, space):
        return space.send(self, space.newsymbol("to_i"))
