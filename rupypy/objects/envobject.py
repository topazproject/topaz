import os

from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object


class W_EnvObject(W_Object):
    classdef = ClassDef("EnviromentVariables", W_Object.classdef)

    @classmethod
    def setup_class(cls, space, w_cls):
        space.set_const(space.w_object, "ENV", cls(space))

    @classdef.method("[]", key="str")
    def method_subscript(self, space, key):
        return space.newstr_fromstr(os.environ[key])
