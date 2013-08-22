from tests.modules.ffi.base import BaseFFITest

from rpython.rtyper.lltypesystem import rffi
from rpython.rtyper.lltypesystem import lltype

class TestMemoryPointer(BaseFFITest):

    def test_its_superclass_is_Pointer(self, space):
        assert self.ask(space,
        "FFI::MemoryPointer.superclass.equal?(FFI::Pointer)")

class TestMemoryPointer__new(BaseFFITest):
    def test_it_sets_up_a_wrapped_type_object(self, ffis):
        w_mem_ptr = ffis.execute("FFI::MemoryPointer.new(:int32, 1)")
        assert w_mem_ptr.w_type == ffis.execute("FFI::Type::INT32")

    def test_it_lets_you_cast_its_content(self, ffis):
        w_ptr = ffis.execute("FFI::MemoryPointer.new(:int16, 4)")
        for ptr, rffi_t in [
                                (w_ptr.char_cast(), rffi.CHAR),
                                (w_ptr.short_cast(), rffi.SHORT),
                                (w_ptr.int_cast(), rffi.INT)
                                  ]:
            assert ptr._TYPE.TO == rffi.CArray(rffi_t)

    def test_it_lets_you_convert_its_size_into_different_units(self, ffis):
        w_mem_ptr = ffis.execute("FFI::MemoryPointer.new(:int16, 4)")
        assert w_mem_ptr.char_size() == 8
        assert w_mem_ptr.short_size() == 4
        assert w_mem_ptr.int_size() == 2

    def test_its_size_argument_defaults_to_1(self, ffis):
        for t in ['char', 'short', 'int']:
            w_ptr1 = ffis.execute("FFI::MemoryPointer.new(:%s, 1)" % t)
            w_ptr2 = ffis.execute("FFI::MemoryPointer.new(:%s)" % t)
            assert w_ptr1.sizeof_memory == w_ptr2.sizeof_memory
