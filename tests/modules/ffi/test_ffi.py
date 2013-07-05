from tests.modules.ffi.base import BaseFFITest
from topaz.objects.hashobject import W_HashObject
from topaz.objects.classobject import W_ClassObject
from topaz.objects.moduleobject import W_ModuleObject
from topaz.modules.ffi.type import W_TypeObject

from rpython.rtyper.lltypesystem import rffi

class TestFFI(BaseFFITest):

    def test_TypeDefs(self, space):
        assert self.ask(space, 'FFI::TypeDefs.kind_of? Hash')

    def test_Types(self, space):
        assert self.ask(space, 'FFI::Types.kind_of? Hash')

    def test_Platform(self, space):
        w_p = space.execute('FFI::Platform')
        assert type(w_p) is W_ModuleObject
        w_res = space.execute('FFI::Platform::INT8_SIZE')
        assert space.int_w(w_res) == rffi.sizeof(rffi.CHAR)
        w_res = space.execute('FFI::Platform::INT16_SIZE')
        assert space.int_w(w_res) == rffi.sizeof(rffi.SHORT)
        w_res = space.execute('FFI::Platform::INT32_SIZE')
        assert space.int_w(w_res) == rffi.sizeof(rffi.INT)
        w_res = space.execute('FFI::Platform::INT64_SIZE')
        assert space.int_w(w_res) == rffi.sizeof(rffi.LONGLONG)
        w_res = space.execute('FFI::Platform::LONG_SIZE')
        assert space.int_w(w_res) == rffi.sizeof(rffi.LONG)
        w_res = space.execute('FFI::Platform::FLOAT_SIZE')
        assert space.int_w(w_res) == rffi.sizeof(rffi.FLOAT)
        w_res = space.execute('FFI::Platform::DOUBLE_SIZE')
        assert space.int_w(w_res) == rffi.sizeof(rffi.DOUBLE)
        w_res = space.execute('FFI::Platform::ADDRESS_SIZE')
        assert space.int_w(w_res) == rffi.sizeof(rffi.VOIDP)

    def test_StructLayout(self, space):
        w_sl = space.execute('FFI::StructLayout')
        assert isinstance(w_sl, W_ClassObject)
        w_res = space.execute('FFI::StructLayout::Field')
        assert w_res == space.w_nil

    def test_StructByReference(self, space):
        w_sbr = space.execute('FFI::StructByReference')
        assert isinstance(w_sbr, W_ClassObject)

    def test_NullPointerError_ihnerits_from_Exception(self, space):
        assert self.ask(space,
        "FFI::NullPointerError.ancestors.include? Exception")
