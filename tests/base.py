from contextlib import contextmanager

import py

from rupypy.error import RubyError
from rupypy.objects.arrayobject import W_ArrayObject
from rupypy.objects.intobject import W_IntObject
from rupypy.objects.floatobject import W_FloatObject
from rupypy.objects.stringobject import W_StringObject
from rupypy.objects.symbolobject import W_SymbolObject
from rupypy.objects.boolobject import W_TrueObject, W_FalseObject

class BaseRuPyPyTest(object):
    @contextmanager
    def raises(self, exc_name):
        with py.test.raises(RubyError) as exc:
            yield
        assert exc.value.w_value.classdef.name == exc_name

    def unwrap(self, space, w_obj):
        if isinstance(w_obj, W_IntObject):
            return space.int_w(w_obj)
        elif isinstance(w_obj, W_FloatObject):
            return space.float_w(w_obj)
        elif isinstance(w_obj, W_StringObject):
            return space.str_w(w_obj)
        elif isinstance(w_obj, W_ArrayObject):
            return [self.unwrap(space, w_x) for w_x in space.listview(w_obj)]
        elif isinstance(w_obj, W_SymbolObject):
            return space.symbol_w(w_obj)
        elif isinstance(w_obj, W_TrueObject) or isinstance(w_obj, W_FalseObject):
            return space.bool_w(w_obj)
        elif w_obj is space.w_nil:
            return None
        raise NotImplementedError(type(w_obj))
