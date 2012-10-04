import os

from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object


class W_EnvObject(W_Object):
    classdef = ClassDef("EnviromentVariables", W_Object.classdef)

    @classmethod
    def setup_class(cls, space, w_cls):
        space.set_const(space.w_object, "ENV", cls(space))

    @classdef.method("[]")
    def method_subscript(self, space, w_key):
        key = space.str_w(space.convert_type(w_key, space.w_string, "to_str"))
        try:
            val = os.environ[key]
        except KeyError:
            return space.w_nil
        return space.newstr_fromstr(val)

    @classdef.method("[]=")
    def method_subscript_assign(self, space, w_key, w_value):
        key = space.str_w(space.convert_type(w_key, space.w_string, "to_str"))
        value = space.str_w(space.convert_type(w_value, space.w_string, "to_str"))
        os.environ[key] = value
        return w_value

    @classdef.method("class")
    def method_class(self, space):
        return space.w_object
