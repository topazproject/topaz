from tests.modules.ffi.base import BaseFFITest

from rpython.rtyper.lltypesystem import rffi
from rpython.rtyper.lltypesystem.llmemory import (cast_ptr_to_adr as ptr2adr,
                                                  cast_adr_to_int as adr2int)

class TestMemoryPointer(BaseFFITest):

    def test_its_superclass_is_Pointer(self, space):
        assert self.ask(space,
        "FFI::MemoryPointer.superclass.equal?(FFI::Pointer)")

class TestMemoryPointer__new(BaseFFITest):
    def test_it_sets_up_a_wrapped_type_object(self, space):
        w_mem_ptr = space.execute("FFI::MemoryPointer.new(:int32, 1)")
        assert w_mem_ptr.w_type == space.execute("FFI::Type::INT32")

    def test_it_lets_you_cast_its_content(self, space):
        w_ptr = space.execute("FFI::MemoryPointer.new(:int16, 4)")
        for ptr, rffi_t in [
                                (w_ptr.int8_cast(), rffi.CHAR),
                                (w_ptr.int16_cast(), rffi.SHORT),
                                (w_ptr.int32_cast(), rffi.INT)
                                  ]:
            assert ptr._TYPE.TO == rffi.CArray(rffi_t)

    def test_it_lets_you_convert_its_size_into_different_units(self, space):
        w_mem_ptr = space.execute("FFI::MemoryPointer.new(:int16, 4)")
        assert w_mem_ptr.int8_size() == 8
        assert w_mem_ptr.int16_size() == 4
        assert w_mem_ptr.int32_size() == 2

    def test_its_size_argument_defaults_to_1(self, space):
        for t in ['char', 'short', 'int']:
            w_ptr1 = space.execute("FFI::MemoryPointer.new(:%s, 1)" % t)
            w_ptr2 = space.execute("FFI::MemoryPointer.new(:%s)" % t)
            assert w_ptr1.sizeof_memory == w_ptr2.sizeof_memory

    def test_it_also_lets_you_read_its_address(self, space):
        w_results = space.execute("""
        mem_ptr = FFI::MemoryPointer.new(:int8, 1)
        [mem_ptr, mem_ptr.address]
        """)
        w_mem_ptr, w_address = space.listview(w_results)
        expected = adr2int(ptr2adr(w_mem_ptr.ptr))
        actual = self.unwrap(space, w_address)
        assert expected == actual
