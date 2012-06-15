import os

from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_BaseObject


class W_Dir(W_BaseObject):
    classdef = ClassDef("Dir", W_BaseObject.classdef)

    @classdef.singleton_method("pwd")
    def method_pwd(self, space):
        return space.newstr_fromstr(os.getcwd())
