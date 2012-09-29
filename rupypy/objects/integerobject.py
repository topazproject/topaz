from rupypy.module import ClassDef
from rupypy.objects.numericobject import W_NumericObject


class W_IntegerObject(W_NumericObject):
    classdef = ClassDef("Integer", W_NumericObject.classdef)

    @classdef.method("to_i")
    def method_to_i(self, space):
        return self
