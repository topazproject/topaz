from contextlib import contextmanager

import pytest

from topaz.error import RubyError
from topaz.objects.arrayobject import W_ArrayObject
from topaz.objects.bignumobject import W_BignumObject
from topaz.objects.boolobject import W_TrueObject, W_FalseObject
from topaz.objects.floatobject import W_FloatObject
from topaz.objects.intobject import W_FixnumObject
from topaz.objects.hashobject import W_HashObject
from topaz.objects.moduleobject import W_ModuleObject
from topaz.objects.stringobject import W_StringObject
from topaz.objects.symbolobject import W_SymbolObject


class BaseTopazTest(object):
    @contextmanager
    def raises(self, space, exc_name, msg=None):
        with pytest.raises(RubyError) as exc:
            yield
        assert space.getclass(exc.value.w_value).name == exc_name
        if msg is not None:
            assert exc.value.w_value.msg == msg

    def find_const(self, space, name):
        return space.find_const(space.w_object, name)

    def unwrap(self, space, w_obj):
        if isinstance(w_obj, W_FixnumObject):
            return space.int_w(w_obj)
        elif isinstance(w_obj, W_BignumObject):
            return space.bigint_w(w_obj)
        elif isinstance(w_obj, W_FloatObject):
            return space.float_w(w_obj)
        elif isinstance(w_obj, W_TrueObject):
            return True
        elif isinstance(w_obj, W_FalseObject):
            return False
        elif isinstance(w_obj, W_StringObject):
            return space.str_w(w_obj)
        elif isinstance(w_obj, W_SymbolObject):
            return space.symbol_w(w_obj)
        elif isinstance(w_obj, W_ArrayObject):
            return [self.unwrap(space, w_x) for w_x in space.listview(w_obj)]
        elif isinstance(w_obj, W_HashObject):
            h = {}
            contents = w_obj.strategy.unerase(w_obj.dict_storage)
            w_hash = contents
            for w_key in w_hash.keys():
                h[self.unwrap(space, w_key)] = self.unwrap(space, w_hash[w_key])
            return h
        elif isinstance(w_obj, W_ModuleObject):
            return w_obj
        elif w_obj is space.w_true:
            return True
        elif w_obj is space.w_false:
            return False
        elif w_obj is space.w_nil:
            return None
        raise NotImplementedError(type(w_obj))
