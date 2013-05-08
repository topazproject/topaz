from ..base import BaseTopazTest
from topaz.modules.ffi import FFI
from topaz.objects.hashobject import W_HashObject
from topaz.objects.classobject import W_ClassObject

class TestFFI(BaseTopazTest):

    primitive_types =  ['INT8', 'UINT8', 'INT16', 'UINT16',
                        'INT32', 'UINT32', 'INT64', 'UINT64',
                        'LONG', 'ULONG', 'FLOAT32', 'FLOAT64',
                        'VOID', 'LONGDOUBLE', 'POINTER', 'BOOL']

    def test_basic(self, space):
        w_type_defs = space.execute('FFI::TypeDefs')
        assert isinstance(w_type_defs, W_HashObject)
        w_types = space.execute('FFI::Types')
        assert isinstance(w_types, W_HashObject)

    def test_FFI_type_constants(self, space):
        # just check, whether the constants even exist for now
        for pt in TestFFI.primitive_types:
            space.execute('FFI::TYPE_%s' % pt)

    def test_Type(self, space):
        w_type = space.execute('FFI::Type')
        assert isinstance(w_type, W_ClassObject)
        for pt in TestFFI.primitive_types:
            w_type.find_const(space, space.newsymbol(pt))
