import os

from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object


class W_Dir(W_Object):
    classdef = ClassDef("Dir", W_Object.classdef)

    @classdef.singleton_method("pwd")
    def method_pwd(self, space):
        return space.newstr_fromstr(os.getcwd())
