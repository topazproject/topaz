import os

from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object


class W_EnvObject(W_Object):
    classdef = ClassDef("EnvironmentVariables", W_Object.classdef)

    def __init__(self, space):
        W_Object.__init__(self, space)
        self.environ = os.environ

    @classmethod
    def setup_class(cls, space, w_cls):
        space.set_const(space.getclassfor(W_Object), "ENV", W_EnvObject(space))

    @classdef.method("[]", key="str")
    def method_subscript(self, space, key):
        value = self.environ.get(key, None)
        if value is None:
            return space.w_nil
        else:
            return space.newstr_fromstr(value)

    @classdef.method("[]=", key="str")
    def method_subscript_assign(self, space, key, w_value):
        self.environ[key] = space.str_w(w_value)
        return w_value

    @classdef.singleton_method("class")
    def method_class(self, space):
        return space.getclassfor(W_Object)
