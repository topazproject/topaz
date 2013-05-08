from ..base import BaseTopazTest
from topaz.modules.ffi import FFI
from topaz.objects.hashobject import W_HashObject
from topaz.objects.classobject import W_ClassObject

class TestFFI(BaseTopazTest):

    def test_basic(self, space):
        w_type_defs = space.execute('FFI::TypeDefs')
        assert isinstance(w_type_defs, W_HashObject)
        w_types = space.execute('FFI::Types')
        assert isinstance(w_types, W_HashObject)
        w_type = space.execute('FFI::Type')
        assert isinstance(w_type, W_ClassObject)
