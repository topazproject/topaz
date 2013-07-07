import errno
import os

from topaz.error import error_for_errno
from topaz.module import ClassDef
from topaz.coerce import Coerce
from topaz.objects.objectobject import W_Object
from topaz.modules.enumerable import Enumerable


class W_EnvObject(W_Object):
    classdef = ClassDef("EnviromentVariables", W_Object.classdef)
    classdef.include_module(Enumerable)

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
        s = space.newstr_fromstr(val)
        space.send(s, "freeze")
        return s

    @classdef.method("store", key="str")
    @classdef.method("[]=", key="str")
    def method_subscript_assign(self, space, key, w_value):
        if "\0" in key:
            raise space.error(space.w_ArgumentError, "bad environment variable name")
        if w_value is space.w_nil:
            try:
                del os.environ[key]
            except (KeyError, OSError):
                pass
            return space.w_nil
        if "=" in key or key == "":
            raise error_for_errno(space, errno.EINVAL)
        value = Coerce.str(space, w_value)
        if "\0" in value:
            raise space.error(space.w_ArgumentError, "bad environment variable value")
        os.environ[key] = value
        return w_value

    @classdef.method("each_pair")
    @classdef.method("each")
    def method_each(self, space, block):
        if block is None:
            return space.send(self, "enum_for", [space.newsymbol("each")])
        for k, v in os.environ.items():
            sk = space.newstr_fromstr(k)
            sv = space.newstr_fromstr(v)
            space.send(sk, "freeze")
            space.send(sv, "freeze")
            space.invoke_block(block, [space.newarray([sk, sv])])
        return self

    @classdef.method("length")
    @classdef.method("size")
    def method_size(self, space):
        return space.newint(len(os.environ.items()))

    @classdef.method("key?", key="str")
    @classdef.method("has_key?", key="str")
    @classdef.method("member?", key="str")
    @classdef.method("include?", key="str")
    def method_includep(self, space, key):
        if "\0" in key:
            raise space.error(space.w_ArgumentError, "bad environment variable name")
        try:
            os.environ[key]
        except KeyError:
            return space.newbool(False)
        return space.newbool(True)
