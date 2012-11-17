from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object


class W_BindingObject(W_Object):
    classdef = ClassDef("Binding", W_Object.classdef)
