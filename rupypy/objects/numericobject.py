from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object, W_BuiltinObject

class W_NumericObject(W_BuiltinObject):
    classdef = ClassDef("Numeric", W_Object.classdef)
