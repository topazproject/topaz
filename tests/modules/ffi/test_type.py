from tests.modules.ffi.base import BaseFFITest
from topaz.modules.ffi.type import (ffi_types, native_types, aliases,
                                    W_TypeObject, W_BuiltinObject)
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

def test_aliases():
    assert aliases['SCHAR'] == 'INT8'
    assert aliases['CHAR'] == 'INT8'
    assert aliases['UCHAR'] == 'UINT8'
    assert aliases['SHORT'] == 'INT16'
    assert aliases['SSHORT'] == 'INT16'
    assert aliases['USHORT'] == 'UINT16'
    assert aliases['INT'] == 'INT32'
    assert aliases['SINT'] == 'INT32'
    assert aliases['UINT'] == 'UINT32'
    assert aliases['LONG_LONG'] == 'INT64'
    assert aliases['SLONG'] == 'LONG'
    assert aliases['SLONG_LONG'] == 'INT64'
    assert aliases['ULONG_LONG'] == 'UINT64'
    assert aliases['FLOAT'] == 'FLOAT32'
    assert aliases['DOUBLE'] == 'FLOAT64'
    assert aliases['STRING'] == 'POINTER'
    assert aliases['BUFFER_IN'] == 'POINTER'
    assert aliases['BUFFER_OUT'] == 'POINTER'
    assert aliases['BUFFER_INOUT'] == 'POINTER'

class TestType(BaseFFITest):
    def test_it_is_a_class(self, space):
        assert self.ask(space, "FFI::Type.is_a? Class")

    def test_it_has_these_attributes_on_the_low_level(self, space):
        w_type = W_TypeObject(space, 'TYPENAME')
        assert w_type.name == 'TYPENAME'

class TestFFI__TestType(BaseFFITest):
    def test_it_is_a_Module(self, space):
        assert self.ask(space, "FFI::NativeType.is_a? Module")

    def test_it_contains_some_type_constants(self, space):
        for typename in ffi_types:
            assert self.ask(space, "FFI::NativeType::%s.is_a? FFI::Type"
                            %typename)

class TestFFI__Type__Builtin(BaseFFITest):
    def test_Builtin_is_a_direct_subclass_of_Type(self, space):
        assert self.ask(space, "FFI::Type::Builtin.superclass.equal? FFI::Type")

    def test_it_has_these_instances_defined_under_Type(self, space):
        for typename in ffi_types:
            assert self.ask(space, "FFI::Type::%s.is_a? FFI::Type::Builtin"
                            % typename)

    def test_its_instances_can_be_accessed_in_different_ways(self, space):
        for typename in ffi_types:
            w_t1 = space.execute('FFI::TYPE_%s' % typename)
            w_t2 = space.execute('FFI::Type::%s' % typename)
            w_t3 = space.execute('FFI::NativeType::%s' % typename)
            assert w_t1 == w_t2
            assert w_t2 == w_t3
        for typename in aliases:
            w_ac = space.execute('FFI::Type::%s' % typename)
            w_ex = space.execute('FFI::Type::%s' % aliases[typename])
            assert w_ac == w_ex

class TestFFI__Type_get_ffi_type(BaseFFITest):
    def test_it_looks_up_the_ffi_type(self, space):
        for typename in ffi_types:
            w_type = space.execute("FFI::Type::%s" %typename)
            t = w_type.get_ffi_type()
            assert t is ffi_types[typename]

class TestFFI__Type_get_native_type(BaseFFITest):
    def test_it_looks_up_the_ffi_type(self, space):
        for typename in native_types:
            w_type = space.execute("FFI::Type::%s" %typename)
            t = w_type.get_native_type()
            assert t is native_types[typename]
