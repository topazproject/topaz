import os

from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object


class W_EnvObject(W_Object):
    classdef = ClassDef("EnviromentVariables", W_Object.classdef, filepath=__file__)

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        space.set_const(space.w_object, "ENV", cls(space))

    @classdef.method("class")
    def method_class(self, space):
        return space.w_object

    @classdef.method("[]", key="str")
    def method_subscript(self, space, key):
        if "\0" in key:
            raise space.error(space.w_ArgumentError, "bad environment variable name")
        try:
            val = os.environ[key]
        except KeyError:
            return space.w_nil
        return space.newstr_fromstr(val)

    @classdef.method("[]=", key="str", value="str")
    def method_subscript_assign(self, space, key, value):
        if "\0" in key:
            raise space.error(space.w_ArgumentError, "bad environment variable name")
        if "\0" in value:
            raise space.error(space.w_ArgumentError, "bad environment variable value")
        os.environ[key] = value
        return space.newstr_fromstr(value)
