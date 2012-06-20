from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object

class W_NumericObject(W_Object):
    classdef = ClassDef("Numeric", W_Object.classdef)
