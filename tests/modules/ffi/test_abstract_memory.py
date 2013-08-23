from tests.modules.ffi.base import BaseFFITest

class TestAbstractMemory__put_int8(BaseFFITest):
    def test_it_puts_a_single_int8_into_the_given_offset(self, ffis):
        w_mem_ptr = ffis.execute("""
        mem_ptr = FFI::MemoryPointer.new(:int8, 2)
        mem_ptr.put_int8(0, 111)
        mem_ptr.put_int8(1, 107)
        mem_ptr
        """)
        int_ptr = w_mem_ptr.int8_cast()
        assert int_ptr[0] == 'o'
        assert int_ptr[1] == 'k'

    def test_it_refuses_negative_offset(self, ffis):
        with self.raises(ffis, 'IndexError',
                         "Memory access offset=-1 size=1 is out of bounds"):
            ffis.execute("""
            FFI::MemoryPointer.new(:int8, 1).put_int8(-1, 230)
            """)

class TestAbstractMemory__write_int8(BaseFFITest):
    def test_it_is_like_calling_put_int8_with_0_as_1st_arg(self, ffis):
        w_mem_ptr = ffis.execute("""
        mem_ptr = FFI::MemoryPointer.new(:int8, 1)
        mem_ptr.write_int8(121)
        mem_ptr
        """)
        assert w_mem_ptr.int8_cast()[0] == 'y'

class TestAbstractMemory__get_int8(BaseFFITest):
    def test_it_gets_a_single_int8_from_the_given_offset(self, ffis):
        w_res = ffis.execute("""
        mem_ptr = FFI::MemoryPointer.new(:int8, 5)
        mem_ptr.put_int8(4, 0)
        mem_ptr.get_int8(4)
        """)
        assert self.unwrap(ffis, w_res) == 0

class TestAbstractMemory__read_int8(BaseFFITest):
    def test_it_is_like_calling_get_int8_with_0(self, ffis):
        w_res = ffis.execute("""
        mem_ptr = FFI::MemoryPointer.new(:int8, 1)
        mem_ptr.write_int8(1)
        mem_ptr.read_int8
        """)
        assert self.unwrap(ffis, w_res) == 1

    def test_it_refuses_negative_offset(self, ffis):
        with self.raises(ffis, 'IndexError',
                         "Memory access offset=-1 size=1 is out of bounds"):
            ffis.execute("""
            FFI::MemoryPointer.new(:int8, 1).get_int8(-1)
            """)

class TestAbstractMemory__put_int32(BaseFFITest):
    def test_it_puts_a_single_int32_into_the_given_offset(self, ffis):
        w_mem_ptr = ffis.execute("""
        mem_ptr = FFI::MemoryPointer.new(:int32, 2)
        mem_ptr.put_int32(0, 2**31 - 1)
        mem_ptr.put_int32(1, 2**31)
        mem_ptr
        """)
        int_ptr = w_mem_ptr.int32_cast()
        assert int_ptr[0] == 2**31 - 1
        assert int_ptr[1] == -2**31

    def test_it_refuses_negative_offset(self, ffis):
        with self.raises(ffis, 'IndexError',
                         "Memory access offset=-1 size=4 is out of bounds"):
            ffis.execute("""
            FFI::MemoryPointer.new(:int32, 1).put_int32(-1, 1073741809)
            """)

    def test_it_refuses_too_large_offset(self, ffis):
        with self.raises(ffis, 'IndexError',
                         "Memory access offset=3 size=4 is out of bounds"):
            ffis.execute("""
            FFI::MemoryPointer.new(:int32, 3).put_int32(3, 1073741809)
            """)

class TestAbstractMemory__write_int32(BaseFFITest):
    def test_it_is_like_calling_put_int32_with_0_as_1st_arg(self, ffis):
        w_mem_ptr = ffis.execute("""
        mem_ptr = FFI::MemoryPointer.new(:int32, 1)
        mem_ptr.write_int32(2**29)
        mem_ptr
        """)
        assert w_mem_ptr.int32_cast()[0] == 2**29

class TestAbstractMemory__get_int32(BaseFFITest):
    def test_it_gets_a_single_int32_from_the_given_offset(self, ffis):
        w_res = ffis.execute("""
        mem_ptr = FFI::MemoryPointer.new(:int32, 5)
        mem_ptr.put_int32(4, 2**30)
        mem_ptr.get_int32(4)
        """)
        assert self.unwrap(ffis, w_res) == 2**30

    def test_it_refuses_negative_offset(self, ffis):
        with self.raises(ffis, 'IndexError',
                         "Memory access offset=-1 size=4 is out of bounds"):
            ffis.execute("""
            FFI::MemoryPointer.new(:int32, 1).get_int32(-1)
            """)

    def test_it_refuses_too_large_offset(self, ffis):
        with self.raises(ffis, 'IndexError',
                         "Memory access offset=6 size=4 is out of bounds"):
            ffis.execute("""
            FFI::MemoryPointer.new(:int32, 6).get_int32(6)
            """)

class TestAbstractMemory__read_int32(BaseFFITest):
    def test_it_is_like_calling_get_int32_with_0(self, ffis):
        w_res = ffis.execute("""
        mem_ptr = FFI::MemoryPointer.new(:int32, 1)
        mem_ptr.write_int32(2**29)
        mem_ptr.read_int32
        """)
        assert self.unwrap(ffis, w_res) == 2**29

#class TestAbstractMemory__put_array_of_int32(BaseFFITest):
#    def test_it_writes_into_array(self, ffis):
#        w_mem_ptr = ffis.execute("""
#        mem_ptr = FFI::MemoryPointer.new(:int32, 10)
#        mem_ptr.put_array_of_int32(0, (0..9).to_a)
#        mem_ptr
#        """)
#        int_ptr = w_mem_ptr.int32_cast()
#        for i in range(10):
#            assert int_ptr[i] == i
#
#    def test_it_refuses_negative_offset(self, ffis):
#        with self.raises(ffis, 'IndexError',
#                         "Memory access offset=-1 size=4 is out of bounds"):
#            ffis.execute("""
#            mem_ptr = FFI::MemoryPointer.new(:int32, 1)
#            mem_ptr.put_array_of_int32(-1, [0])
#            """)
#
#    def test_it_refuses_too_large_offset(self, ffis):
#        with self.raises(ffis, 'IndexError',
#                         "Memory access offset=3 size=4 is out of bounds"):
#            w_mem_ptr = ffis.execute("""
#            mem_ptr = FFI::MemoryPointer.new(:int32, 3)
#            mem_ptr.put_array_of_int32(3, [13])
#            """)
#
#    def test_it_refuses_too_large_offset_even_without_writing(self, ffis):
#        with self.raises(ffis, 'IndexError',
#                         "Memory access offset=5 size=0 is out of bounds"):
#            w_mem_ptr = ffis.execute("""
#            mem_ptr = FFI::MemoryPointer.new(:int32, 5)
#            mem_ptr.put_array_of_int32(5, [])
#            """)
#
#    def test_it_refuses_too_big_array(self, ffis):
#        with self.raises(ffis, 'IndexError',
#                         "Memory access offset=0 size=12 is out of bounds"):
#            w_mem_ptr = ffis.execute("""
#            mem_ptr = FFI::MemoryPointer.new(:int32, 2)
#            mem_ptr.put_array_of_int32(0, [1, 2, 3])
#            """)
#
#class TestAbstractMemory__get_array_of_int32(BaseFFITest):
#    def test_it_reads_from_array(self, ffis):
#        w_res = ffis.execute("""
#        mem_ptr = FFI::MemoryPointer.new(:int32, 10)
#        mem_ptr.put_array_of_int32(0, (0..9).to_a)
#        mem_ptr.get_array_of_int32(0, 10)
#        """)
#        assert self.unwrap(ffis, w_res) == range(10)
