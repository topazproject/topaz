from tests.modules.ffi.base import BaseFFITest
from topaz.modules.ffi.buffer import W_BufferObject

from rpython.rtyper.lltypesystem import rffi
from rpython.rtyper.lltypesystem import lltype

class TestMemoryPointer(BaseFFITest):

    def test_it_inherits_from_Pointer(self, space):
        assert self.ask(space,
        "FFI::MemoryPointer.ancestors.include? FFI::Pointer")

class TestMemoryPointer__new(BaseFFITest):
    def test_it_sets_up_a_wrapped_type_object(self, ffis):
        w_mem_ptr = ffis.execute("FFI::MemoryPointer.new(:int32, 1)")
        assert w_mem_ptr.w_type == ffis.execute("FFI::Type::INT32")

    def test_it_sets_up_a_c_array(self, ffis):
        w_mem_ptr = ffis.execute("FFI::MemoryPointer.new(:int8, 5)")
        assert isinstance(w_mem_ptr.ptr, lltype._ptr)
        assert w_mem_ptr._size == 5
        assert w_mem_ptr.ptr._obj.getlength() == w_mem_ptr._size
        lltype.free(w_mem_ptr.ptr, flavor='raw')

class TestMemoryPointer__put_array_of_int32(BaseFFITest):
    def test_it_writes_into_array(self, ffis):
        w_mem_ptr = ffis.execute("""
        mem_ptr = FFI::MemoryPointer.new(:int32, 10)
        mem_ptr.put_array_of_int32(0, (0..9).to_a)
        mem_ptr
        """)
        assert w_mem_ptr.ptr._obj.items == range(10)

    def test_it_refuses_negative_offset(self, ffis):
        with self.raises(ffis, 'IndexError',
                         "Memory access offset=-1 size=4 is out of bounds"):
            ffis.execute("""
            mem_ptr = FFI::MemoryPointer.new(:int32, 1)
            mem_ptr.put_array_of_int32(-1, [0])
            """)

    def test_it_refuses_too_large_offset(self, ffis):
        with self.raises(ffis, 'IndexError',
                         "Memory access offset=3 size=4 is out of bounds"):
            w_mem_ptr = ffis.execute("""
            mem_ptr = FFI::MemoryPointer.new(:int32, 3)
            mem_ptr.put_array_of_int32(3, [13])
            """)

    def test_it_refuses_too_large_offset_even_without_writing(self, ffis):
        with self.raises(ffis, 'IndexError',
                         "Memory access offset=5 size=0 is out of bounds"):
            w_mem_ptr = ffis.execute("""
            mem_ptr = FFI::MemoryPointer.new(:int32, 5)
            mem_ptr.put_array_of_int32(5, [])
            """)

    def test_it_refuses_too_big_array(self, ffis):
        with self.raises(ffis, 'IndexError',
                         "Memory access offset=0 size=12 is out of bounds"):
            w_mem_ptr = ffis.execute("""
            mem_ptr = FFI::MemoryPointer.new(:int32, 2)
            mem_ptr.put_array_of_int32(0, [1, 2, 3])
            """)

class TestMemoryPointer__get_array_of_int32(BaseFFITest):
    def test_it_reads_from_array(self, ffis):
        w_res = ffis.execute("""
        mem_ptr = FFI::MemoryPointer.new(:int32, 10)
        mem_ptr.put_array_of_int32(0, (0..9).to_a)
        mem_ptr.get_array_of_int32(0, 10)
        """)
        assert self.unwrap(ffis, w_res) == range(10)
