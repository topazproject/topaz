from topaz.objects.objectobject import W_Object
from topaz.module import ClassDef

class W_TypeObject(W_Object):
    classdef = ClassDef('Type', W_Object.classdef)

    def __init__(self, space, native_type, ffi_type, klass=None):
        W_Object.__init__(self, space, klass)
        self.native_type = native_type
        self.ffi_type = ffi_type
