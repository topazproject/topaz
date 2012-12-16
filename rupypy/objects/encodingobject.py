from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object


class W_EncodingObject(W_Object):
    classdef = ClassDef("Encoding", W_Object.classdef, filepath=__file__)
