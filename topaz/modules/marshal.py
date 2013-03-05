# http://daeken.com/python-marshal-format

from __future__ import absolute_import
from topaz.module import Module, ModuleDef
from topaz.objects.arrayobject import W_ArrayObject
from topaz.objects.boolobject import W_TrueObject, W_FalseObject
from topaz.objects.intobject import W_FixnumObject
from topaz.objects.nilobject import W_NilObject
from topaz.objects.stringobject import W_StringObject
import marshal


class Marshal(Module):
    moduledef = ModuleDef("Marshal", filepath=__file__)

    @staticmethod
    def dump(space, w_obj):
        if isinstance(w_obj, W_TrueObject):
            obj = True
        elif isinstance(w_obj, W_FalseObject):
            obj = False
        elif isinstance(w_obj, W_NilObject):
            obj = None
        elif isinstance(w_obj, W_FixnumObject):
            obj = space.int_w(w_obj)
        elif isinstance(w_obj, W_StringObject):
            obj = space.str_w(w_obj)
        elif isinstance(w_obj, W_ArrayObject):
            obj = []
            for w_item in w_obj.items_w:
                obj.append(Marshal.dump(space, w_item))
        else:
            raise NotImplementedError(type(w_obj))

        return obj

    @staticmethod
    def load(space, obj):
        if obj is True:
            return space.w_true
        elif obj is False:
            return space.w_false
        elif obj is None:
            return space.w_nil
        elif isinstance(obj, int):
            return space.newint(obj)
        elif isinstance(obj, str):
            return space.newstr_fromstr(obj)
        elif isinstance(obj, list):
            array = []
            for item in obj:
                array.append(Marshal.load(space, item))
            return space.newarray(array)
        else:
            raise NotImplementedError(format)

    @moduledef.function("dump")
    def method_dump(self, space, w_obj):
        obj = Marshal.dump(space, w_obj)
        return space.newstr_fromstr(marshal.dumps(obj))

    @moduledef.function("load")
    def method_load(self, space, w_obj):
        dump = space.str_w(w_obj)
        obj = marshal.loads(dump)
        return Marshal.load(space, obj)
