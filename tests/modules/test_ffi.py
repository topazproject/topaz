from ..base import BaseTopazTest
from topaz.modules.ffi import FFI
from topaz.objects.hashobject import W_HashObject
from topaz.objects.classobject import W_ClassObject
from topaz.objects.moduleobject import W_ModuleObject

class TestFFI(BaseTopazTest):

    primitive_types =  ['INT8', 'UINT8', 'INT16', 'UINT16',
                        'INT32', 'UINT32', 'INT64', 'UINT64',
                        'LONG', 'ULONG', 'FLOAT32', 'FLOAT64',
                        'VOID', 'LONGDOUBLE', 'POINTER', 'BOOL']
    alias_types = ['SCHAR', 'CHAR', 'UCHAR',
                   'SHORT', 'SSHORT', 'USHORT',
                   'INT', 'SINT', 'UINT',
                   'LONG_LONG', 'SLONG', 'SLONG_LONG', 'ULONG_LONG',
                   'FLOAT', 'DOUBLE', 'STRING',
                   'BUFFER_IN', 'BUFFER_OUT', 'BUFFER_INOUT', 'VARARGS']

    def test_basic(self, space):
        w_type_defs = space.execute('FFI::TypeDefs')
        assert isinstance(w_type_defs, W_HashObject)
        w_types = space.execute('FFI::Types')
        assert isinstance(w_types, W_HashObject)

    def test_FFI_type_constants(self, space):
        # just check, whether the constants even exist for now
        for pt in TestFFI.primitive_types:
            space.execute('FFI::TYPE_%s' % pt)

    #def test_Mapped(self, space):
    #    space.execute("Mapped.new(42)")

    def test_Type(self, space):
        w_type = space.execute('FFI::Type')
        assert isinstance(w_type, W_ClassObject)
        for pt in TestFFI.primitive_types:
            space.execute('FFI::Type::%s' %pt)
        for at in TestFFI.alias_types:
            space.execute('FFI::Type::%s' %at)
        w_mapped = space.execute('FFI::Type::Mapped')
        assert isinstance(w_mapped, W_ClassObject)
        w_res = space.execute('FFI::Type::Mapped.respond_to? :method_missing')
        assert self.unwrap(space, w_res)
        w_res = space.execute('FFI::Type::Mapped.new(42)')

    def test_DataConverter(self, space):
        w_dc = space.execute('FFI::DataConverter')
        assert isinstance(w_dc, W_ModuleObject)
        w_res = space.execute('FFI::DataConverter.native_type(0)')
        assert w_res == space.w_nil
        w_res = space.execute('FFI::DataConverter.to_native')
        assert w_res == space.w_nil
        w_res = space.execute('FFI::DataConverter.from_native')
        assert w_res == space.w_nil

    def test_DynamicLibrary(self, space):
        w_res = space.execute('FFI::DynamicLibrary')
        assert w_res == space.w_nil
