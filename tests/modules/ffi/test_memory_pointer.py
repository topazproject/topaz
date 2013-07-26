from tests.modules.ffi.base import BaseFFITest
from topaz.modules.ffi.buffer import W_BufferObject

from rpython.rtyper.lltypesystem import rffi

class TestMemoryPointer(BaseFFITest):

    def test_it_inherits_from_Pointer(self, space):
        assert self.ask(space,
        "FFI::MemoryPointer.ancestors.include? FFI::Pointer")

class TestMemoryPointer__new(BaseFFITest):
    def test_it_sets_up_a_wrapped_type_object(self, ffis):
        w_mem_ptr = ffis.execute("FFI::MemoryPointer.new(:int32, 1)")
        assert w_mem_ptr.w_type == ffis.execute("FFI::Type::INT32")

    def test_it_sets_up_a_fixed_size_list(self, ffis):
        w_mem_ptr = ffis.execute("FFI::MemoryPointer.new(:int8, 5)")
        assert w_mem_ptr.content == [0]*5

class TestMemoryPointer__put_methods(BaseFFITest):
    def test_put_array_of_int32_writes_into_array(self, ffis):
        w_mem_ptr = ffis.execute("""
        mem_ptr = FFI::MemoryPointer.new(:int32, 10)
        mem_ptr.put_array_of_int32(0, (0..9).to_a)
        mem_ptr
        """)
        assert w_mem_ptr.content == range(10)

    def test_get_array_of_int32_reads_from_array(self, ffis):
        w_res = ffis.execute("""
        mem_ptr = FFI::MemoryPointer.new(:int32, 10)
        mem_ptr.put_array_of_int32(0, (0..9).to_a)
        mem_ptr.get_array_of_int32(0, 10)
        """)
        assert self.unwrap(ffis, w_res) == range(10)
