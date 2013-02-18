from topaz.module import ClassDef
from topaz.objects.numericobject import W_NumericObject


class W_IntegerObject(W_NumericObject):
    classdef = ClassDef("Integer", W_NumericObject.classdef, filepath=__file__)

    @classdef.method("to_i")
    def method_to_i(self, space):
        return self
