from tests.base import BaseTopazTest
from topaz.modules.ffi.type import W_TypeObject, W_BuiltinObject
from topaz.objects.classobject import W_ClassObject
from topaz.objects.moduleobject import W_ModuleObject
from rpython.rlib import clibffi
from rpython.rtyper.lltypesystem import rffi

class TestType(BaseTopazTest):

    primitive_types =  {'INT8': {'size': 1},
                        'UINT8': {'size': 1},
                        'INT16': {'size': 2},
                        'UINT16': {'size': 2},
                        'INT32': {'size': 4},
                        'UINT32': {'size': 4},
                        'INT64': {'size': 8},
                        'UINT64': {'size': 8},
                        'LONG': {'size': rffi.sizeof(rffi.LONG)},
                        'ULONG': {'size': rffi.sizeof(rffi.ULONG)},
                        'FLOAT32': {'size': 4},
                        'FLOAT64': {'size': 8},
                        'VOID': {'size': 1},
                        'LONGDOUBLE': {'size': 16},
                        'POINTER': {'size': 8},
                        'BOOL': {'size': 1},
                        'VARARGS': {'size': 1}}

    def test_aliases(self, space):
        assert W_TypeObject.aliases['SCHAR'] == 'INT8'
        assert W_TypeObject.aliases['CHAR'] == 'INT8'
        assert W_TypeObject.aliases['UCHAR'] == 'UINT8'
        assert W_TypeObject.aliases['SHORT'] == 'INT16'
        assert W_TypeObject.aliases['SSHORT'] == 'INT16'
        assert W_TypeObject.aliases['USHORT'] == 'UINT16'
        assert W_TypeObject.aliases['INT'] == 'INT32'
        assert W_TypeObject.aliases['SINT'] == 'INT32'
        assert W_TypeObject.aliases['UINT'] == 'UINT32'
        assert W_TypeObject.aliases['LONG_LONG'] == 'INT64'
        assert W_TypeObject.aliases['SLONG'] == 'LONG'
        assert W_TypeObject.aliases['SLONG_LONG'] == 'INT64'
        assert W_TypeObject.aliases['ULONG_LONG'] == 'UINT64'
        assert W_TypeObject.aliases['FLOAT'] == 'FLOAT32'
        assert W_TypeObject.aliases['DOUBLE'] == 'FLOAT64'
        assert W_TypeObject.aliases['STRING'] == 'POINTER'
        assert W_TypeObject.aliases['BUFFER_IN'] == 'POINTER'
        assert W_TypeObject.aliases['BUFFER_OUT'] == 'POINTER'
        assert W_TypeObject.aliases['BUFFER_INOUT'] == 'POINTER'

    def test_NativeType(self, space):
        w_native_type = space.execute('FFI::NativeType')
        assert isinstance(w_native_type, W_ModuleObject)
        for pt in TestType.primitive_types:
            space.execute('FFI::NativeType::%s' %pt)

    def test_Type_ll(self, space):
        w_type = W_TypeObject(space, 'TESTVOID', clibffi.ffi_type_void)
        assert w_type.native_type == 'TESTVOID'
        assert w_type.ffi_type is clibffi.ffi_type_void

    def test_Builtin_ll(self, space):
        w_testint = W_TypeObject(space, 'TESTBOOL', clibffi.ffi_type_uchar)
        w_builtin = W_BuiltinObject(space, 'BUILTIN_TESTBOOL', w_testint)
        assert w_builtin.typename == 'BUILTIN_TESTBOOL'
        assert w_builtin.native_type == w_testint.native_type
        assert w_builtin.ffi_type == w_testint.ffi_type

    def test_Type(self, space):
        w_type = space.execute('FFI::Type')
        assert isinstance(w_type, W_ClassObject)

    def test_Builtin(self, space):
        w_builtin = space.execute('FFI::Type::Builtin')
        assert isinstance(w_builtin, W_ClassObject)
        w_type = space.execute('FFI::Type')
        assert w_builtin.superclass is w_type

    def test_Builtin_instances(self, space):
        for pt in TestType.primitive_types:
            w_res = space.execute("FFI::Type::%s.size" % pt)
            assert (self.unwrap(space, w_res) ==
                    TestType.primitive_types[pt]['size'])

    def test_ways_to_access_Builtin_instances(self, space):
        for pt in TestType.primitive_types:
            w_t1 = space.execute('FFI::TYPE_%s' % pt)
            w_t2 = space.execute('FFI::Type::%s' % pt)
            w_t3 = space.execute('FFI::NativeType::%s' % pt)
            assert w_t1 == w_t2
            assert w_t2 == w_t3
        for at in W_TypeObject.aliases:
            w_ac = space.execute('FFI::Type::%s' % at)
            w_ex = space.execute('FFI::Type::%s' % W_TypeObject.aliases[at])
            assert w_ac == w_ex

    def test_Mapped(self, space):
        w_mapped = space.execute('FFI::Type::Mapped')
        assert isinstance(w_mapped, W_ClassObject)
        w_res = space.execute('FFI::Type::Mapped.respond_to? :method_missing')
        assert self.unwrap(space, w_res)
        w_res = space.execute('FFI::Type::Mapped.new(42)')
