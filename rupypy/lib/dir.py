from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_BaseObject


class W_Dir(W_BaseObject):
    classdef = ClassDef("Dir", W_BaseObject.classdef)
