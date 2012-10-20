from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object


class W_ThreadObject(W_Object):
    classdef = ClassDef("Thread", W_Object.classdef)
