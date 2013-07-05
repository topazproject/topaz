from tests.modules.ffi.base import BaseFFITest
from topaz.modules.ffi.type import W_TypeObject, W_BuiltinObject
from topaz.objects.classobject import W_ClassObject
from topaz.objects.moduleobject import W_ModuleObject
from rpython.rlib import clibffi
from rpython.rtyper.lltypesystem import rffi

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

class TestType(BaseFFITest):
    def test_it_defines_these_aliases(self, space):
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

    def test_it_is_a_class(self, space):
        assert self.ask(space, "FFI::Type.is_a? Class")

    def test_it_has_these_attributes_on_the_low_level(self, space):
        w_type = W_TypeObject(space, 'TESTVOID', clibffi.ffi_type_void)
        assert w_type.native_type == 'TESTVOID'
        assert w_type.ffi_type is clibffi.ffi_type_void

class TestFFI__TestType(BaseFFITest):
    def test_it_is_a_Module(self, space):
        assert self.ask(space, "FFI::NativeType.is_a? Module")

    def test_it_contains_some_type_constants(self, space):
        for pt in primitive_types:
            w_res = space.execute('FFI::NativeType::%s.size' %pt)
            assert self.unwrap(space, w_res) == primitive_types[pt]['size']

class TestFFI__Type__Builtin(BaseFFITest):
    def test_it_looks_like_this_on_the_low_level(self, space):
        w_testint = W_TypeObject(space, 'TESTBOOL', clibffi.ffi_type_uchar)
        w_builtin = W_BuiltinObject(space, 'BUILTIN_TESTBOOL', w_testint)
        assert w_builtin.typename == 'BUILTIN_TESTBOOL'
        assert w_builtin.native_type == w_testint.native_type
        assert w_builtin.ffi_type == w_testint.ffi_type

    def test_Builtin_is_a_direct_subclass_of_Type(self, space):
        assert self.ask(space, "FFI::Type::Builtin.superclass.equal? FFI::Type")

    def test_it_has_these_instances_defined_under_Type(self, space):
        for pt in primitive_types:
            w_res = space.execute("FFI::Type::%s.size" % pt)
            assert (self.unwrap(space, w_res) ==
                    primitive_types[pt]['size'])

    def test_its_instances_can_be_accessed_in_different_ways(self, space):
        for pt in primitive_types:
            w_t1 = space.execute('FFI::TYPE_%s' % pt)
            w_t2 = space.execute('FFI::Type::%s' % pt)
            w_t3 = space.execute('FFI::NativeType::%s' % pt)
            assert w_t1 == w_t2
            assert w_t2 == w_t3
        for at in W_TypeObject.aliases:
            w_ac = space.execute('FFI::Type::%s' % at)
            w_ex = space.execute('FFI::Type::%s' % W_TypeObject.aliases[at])
            assert w_ac == w_ex
