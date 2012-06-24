from rupypy.module import ClassDef
from rupypy.objects.numericobject import W_NumericObject

class W_IntegerObject(W_NumericObject):
    classdef = ClassDef("Integer", W_NumericObject.classdef)
