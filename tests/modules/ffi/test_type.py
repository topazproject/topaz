from tests.modules.ffi.base import BaseFFITest
from topaz.modules.ffi.type import (ffi_types, native_types,
                                    W_TypeObject)
from topaz.objects.classobject import W_ClassObject
from topaz.objects.moduleobject import W_ModuleObject
from rpython.rlib import clibffi
from rpython.rtyper.lltypesystem import rffi

def test_aliases():
    assert ffi_types['SCHAR'] == ffi_types['INT8']
    assert ffi_types['CHAR'] == ffi_types['INT8']
    assert ffi_types['UCHAR'] == ffi_types['UINT8']
    assert ffi_types['SHORT'] == ffi_types['INT16']
    assert ffi_types['SSHORT'] == ffi_types['INT16']
    assert ffi_types['USHORT'] == ffi_types['UINT16']
    assert ffi_types['INT'] == ffi_types['INT32']
    assert ffi_types['SINT'] == ffi_types['INT32']
    assert ffi_types['UINT'] == ffi_types['UINT32']
    assert ffi_types['LONG_LONG'] == ffi_types['INT64']
    assert ffi_types['SLONG'] == ffi_types['LONG']
    assert ffi_types['SLONG_LONG'] == ffi_types['INT64']
    assert ffi_types['ULONG_LONG'] == ffi_types['UINT64']
    assert ffi_types['FLOAT'] == ffi_types['FLOAT32']
    assert ffi_types['DOUBLE'] == ffi_types['FLOAT64']
    assert ffi_types['STRING'] == ffi_types['POINTER']
    assert ffi_types['BUFFER_IN'] == ffi_types['POINTER']
    assert ffi_types['BUFFER_OUT'] == ffi_types['POINTER']
    assert ffi_types['BUFFER_INOUT'] == ffi_types['POINTER']

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

    def test_it_has_these_instances_defined_as_constants(self, space):
        for typename in ffi_types:
            assert self.ask(space, "FFI::Type::%s.is_a? FFI::Type"
                            % typename)

    def test_its_instances_can_be_accessed_in_different_ways(self, space):
        for typename in ffi_types:
            w_t1 = space.execute('FFI::TYPE_%s' % typename)
            w_t2 = space.execute('FFI::Type::%s' % typename)
            w_t3 = space.execute('FFI::NativeType::%s' % typename)
            assert w_t1 == w_t2
            assert w_t2 == w_t3

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

class TestFFI__Type_size(BaseFFITest):
    def test_it_returns_the_size_type(self, space):
        w_res = space.execute("FFI::Type::INT8.size")
        assert self.unwrap(space, w_res) == 1
        w_res = space.execute("FFI::Type::INT16.size")
        assert self.unwrap(space, w_res) == 2
        w_res = space.execute("FFI::Type::INT32.size")
        assert self.unwrap(space, w_res) == 4
