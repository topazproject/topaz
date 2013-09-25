from tests.modules.ffi.base import BaseFFITest
from topaz.modules.ffi.abstract_memory import new_cast_method
from topaz.modules.ffi.type import size_for_name, UINT64

from rpython.rtyper.lltypesystem import rffi

import sys

test_put_method_group = ['int16', 'int32', 'int64',
                         'uint8', 'uint16', 'uint32', 'uint64',
                         'float64']
test_get_method_group = ['int8', 'int16', 'int32', 'int64',
                         'uint8', 'uint16', 'uint32',
                         'float64']
test_rw_method_group = ['int8', 'int16', 'int32', 'int64',
                        'uint8', 'uint16', 'uint32',
                        'float32', 'float64']

minval = {}
maxval = {}
for bits in [8, 16, 32, 64]:
    minval['int' + str(bits)] = -2**(bits-1)
    minval['uint' + str(bits)] = 0
    maxval['int' + str(bits)] = 2**(bits-1) - 1
    maxval['uint' + str(bits)] = 2**bits - 1
minval['long'] = -2**(8*rffi.sizeof(rffi.LONG))
minval['ulong'] = 0
maxval['long'] = 2**(8*rffi.sizeof(rffi.LONG)) - 1
maxval['ulong'] = 2**(8*rffi.sizeof(rffi.LONG)-1) - 1
minval['float32'] = 1.175494351e-38
maxval['float32'] = 3.402823466e+38
minval['float64'] = sys.float_info.min
maxval['float64'] = sys.float_info.max

def put_method_test_code(typename):
    # For some reason, str(some_float) cuts off a few digits.
    # Only repr prints the entire float.
    strfunc = ((lambda x: repr(x)) if 'float' in typename else
               (lambda x: str(x)))
    return ("""
    mem_ptr = FFI::MemoryPointer.new(:T, 2)
    mem_ptr.put_T(0, MIN)
    mem_ptr.put_T(1, MAX)
    mem_ptr
    """.replace('T', typename).
        replace('MIN', strfunc(minval[typename])).
        replace('MAX', strfunc(maxval[typename])))

def get_method_test_code(typename):
    strfunc = ((lambda x: repr(x)) if 'float' in typename else
               (lambda x: str(x)))
    return ("""
    mem_ptr = FFI::MemoryPointer.new(:T, 5)
    mem_ptr.put_T(3, MIN)
    mem_ptr.put_T(4, MAX)
    [mem_ptr.get_T(3), mem_ptr.get_T(4)]
    """.replace('T', typename).
        replace('MIN', strfunc(minval[typename])).
        replace('MAX', strfunc(maxval[typename])))

class TestAbstractMemory_put_methods(BaseFFITest):
    def test_they_put_a_single_value_into_the_given_offset(self, ffis):
        for t in test_put_method_group:
            w_mem_ptr = ffis.execute(put_method_test_code(t))
            cast_method = getattr(w_mem_ptr, t + '_cast')
            casted_ptr = cast_method()
            expected_0 = minval[t]
            expected_1 = maxval[t]
            assert expected_0 == casted_ptr[0]
            assert expected_1 == casted_ptr[1]

    def test_they_refuse_negative_offsets(self, ffis):
        for t in test_put_method_group:
            sizeof_t = size_for_name(t.upper())
            with self.raises(ffis, 'IndexError',
                             "Memory access offset=-1 size=%s is out of bounds"
                             %  sizeof_t):
                ffis.execute("""
                FFI::MemoryPointer.new(:T, 1).put_T(-1, 230)
                """.replace('T', t))

    def test_they_refuse_too_large_offsets(self, ffis):
        for t in test_put_method_group:
            sizeof_t = size_for_name(t.upper())
            with self.raises(ffis, 'IndexError',
                             "Memory access offset=3 size=%s is out of bounds"
                             % sizeof_t):
                ffis.execute("""
                FFI::MemoryPointer.new(:T, 3).put_T(3, 15)
                """.replace('T', t))

class TestAbstractMemory_write_methods(BaseFFITest):
    def test_they_are_like_calling_put_with_0_as_1st_arg(self, ffis):
        for t in test_rw_method_group:
            w_mem_ptr = ffis.execute("""
            mem_ptr = FFI::MemoryPointer.new(:T, 1)
            mem_ptr.write_T(121)
            mem_ptr
            """.replace('T', t))
            cast_method = getattr(w_mem_ptr, t + '_cast')
            casted_ptr = cast_method()
            assert casted_ptr[0] == 'y' if t == 'int8' else 121

class TestAbstractMemory_get_methods(BaseFFITest):
    def test_they_get_a_single_value_from_the_given_offset(self, ffis):
        for t in test_get_method_group:
            w_res = ffis.execute(get_method_test_code(t))
            assert self.unwrap(ffis, w_res) == [minval[t], maxval[t]]

class TestAbstractMemory_read_methods(BaseFFITest):
    def test_they_are_like_calling_get_with_0(self, ffis):
        for t in test_rw_method_group:
            w_res = ffis.execute("""
            mem_ptr = FFI::MemoryPointer.new(:T, 1)
            mem_ptr.write_T(1)
            mem_ptr.read_T
            """.replace('T', t))
            assert self.unwrap(ffis, w_res) == 1

class TestAbstractMemory_put_int8(BaseFFITest):
    def test_it_puts_a_single_int8_into_the_given_offset(self, ffis):
        w_mem_ptr = ffis.execute(put_method_test_code('int8'))
        casted_ptr = w_mem_ptr.int8_cast()
        assert casted_ptr[0] == rffi.cast(rffi.CHAR, -128)
        assert casted_ptr[1] == rffi.cast(rffi.CHAR, 127)

class TestAbstractMemory_put_float32(BaseFFITest):
    def test_it_puts_only_one_float32_into_the_given_offset(self, ffis):
        w_mem_ptr = ffis.execute(put_method_test_code('float32'))
        mem_ptr = w_mem_ptr.float32_cast()
        res0, res1 = float(mem_ptr[0]), float(mem_ptr[1])
        # It might only be approximately equal
        assert abs((minval['float32'] - res0) / res0) < 1e-9
        assert abs((maxval['float32'] - res1) / res1) < 1e-9

class TestAbstractMemory_put_pointer(BaseFFITest):
    def test_it_puts_a_single_pointer_into_the_given_offset(self, ffis):
        w_mem_ptr = ffis.execute("""
        mem_ptr = FFI::MemoryPointer.new(:pointer, 2)
        ptr1 = FFI::Pointer.new(88)
        ptr2 = FFI::Pointer.new(55)
        mem_ptr.put_pointer(0, ptr1)
        mem_ptr.put_pointer(1, ptr2)
        mem_ptr
        """)
        w_adr_ptr = new_cast_method(UINT64)(w_mem_ptr)
        assert w_adr_ptr[0] == 88
        assert w_adr_ptr[1] == 55

class TestAbstractMemory_get_float32(BaseFFITest):
    def test_it_gets_only_one_float32_from_the_given_offset(self, ffis):
        w_res = ffis.execute(get_method_test_code('float32'))
        res = self.unwrap(ffis, w_res)
        # It might only be approximately equal
        assert abs((res[0] - minval['float32'])/res[0]) < 1e-9
        assert abs((res[1] - maxval['float32'])/res[1]) < 1e-9

class TestAbstractMemory_get_uint64(BaseFFITest):
    def test_it_gets_a_single_uint64_from_the_given_offset(self, ffis):
        w_res = ffis.execute(get_method_test_code('uint64'))
        res = self.unwrap(ffis, w_res)
        assert res[0].tolong() == minval['uint64']
        assert res[1].tolong() == maxval['uint64']

class TestAbstractMemory_get_pointer(BaseFFITest):
    def test_it_gets_a_single_pointer_from_the_given_offset(self, ffis):
        assert self.ask(ffis, """
        mem_ptr = FFI::MemoryPointer.new(:pointer, 4)
        mem_ptr.put_pointer(3, FFI::Pointer.new(67))
        ptr = mem_ptr.get_pointer(3)
        ptr.class.equal?(FFI::Pointer) and ptr.address == 67
        """)

    def test_it_always_returns_a_simple_pointer(self, ffis):
        assert self.ask(ffis, """
        outer_mem_ptr = FFI::MemoryPointer.new(:pointer, 1)
        inner_mem_ptr = FFI::MemoryPointer.new(:int8, 1)
        outer_mem_ptr.put_pointer(0, inner_mem_ptr)
        ! outer_mem_ptr.get_pointer(0).class.equal? FFI::MemoryPointer
        outer_mem_ptr.get_pointer(0).class.equal? FFI::Pointer
        """)

    def test_it_doesnt_loose_the_content(self, ffis):
        w_res = ffis.execute("""
        outer_mem_ptr = FFI::MemoryPointer.new(:pointer, 1)
        inner_mem_ptr = FFI::MemoryPointer.new(:int16, 1)
        inner_mem_ptr.write_int16(300)
        outer_mem_ptr.put_pointer(0, inner_mem_ptr)
        outer_mem_ptr.get_pointer(0).read_int16
        """)
        assert self.unwrap(ffis, w_res) == 300

class TestAbstractMemory_write_pointer(BaseFFITest):
    def test_it_is_like_calling_put_pointer_with_0_as_1st_arg(self, ffis):
        w_res = ffis.execute("""
        mem_ptr = FFI::MemoryPointer.new(:pointer, 1)
        mem_ptr.write_pointer(FFI::Pointer.new(11))
        mem_ptr.get_pointer(0).address
        """)
        assert self.unwrap(ffis, w_res) == 11

class TestAbstractMemory_write_uint64(BaseFFITest):
    def test_it_is_like_calling_put_uint64_with_0_as_1st_arg(self, ffis):
        w_res = ffis.execute("""
        mem_ptr = FFI::MemoryPointer.new(:uint64, 1)
        mem_ptr.write_uint64(14)
        mem_ptr.get_uint64(0)
        """)
        assert self.unwrap(ffis, w_res) == 14

class TestAbstractMemory_read_pointer(BaseFFITest):
    def test_it_is_like_calling_get_pointer_with_0(self, ffis):
        w_res = ffis.execute("""
        mem_ptr = FFI::MemoryPointer.new(:pointer, 1)
        mem_ptr.put_pointer(0, FFI::Pointer.new(13))
        mem_ptr.read_pointer.address
        """)
        assert self.unwrap(ffis, w_res) == 13

class TestAbstractMemory_read_uint64(BaseFFITest):
    def test_it_is_like_calling_get_uint64_with_0(self, ffis):
        w_res = ffis.execute("""
        mem_ptr = FFI::MemoryPointer.new(:uint64, 1)
        mem_ptr.put_uint64(0, 12)
        mem_ptr.read_uint64
        """)
        assert self.unwrap(ffis, w_res) == 12

class TestAbstractMemory(BaseFFITest):
    def test_it_defines_the_following_aliases(self, space):
        for aliases in [
                        ('int8', 'char'),
                        ('uint8', 'uchar'),
                        ('int16', 'short'),
                        ('uint16', 'ushort'),
                        ('int32', 'int'),
                        ('uint32', 'uint'),
                        ('int64', 'long_long'),
                        ('uint64', 'ulong_long'),
                        ('float32', 'float'),
                        ('float64', 'double')
                       ]:
            assert self.ask(space, """
            FFI::AbstractMemory.instance_method(:put_%s) ==
            FFI::AbstractMemory.instance_method(:put_%s)
            """ % aliases)
            assert self.ask(space, """
            FFI::AbstractMemory.instance_method(:get_%s) ==
            FFI::AbstractMemory.instance_method(:get_%s)
            """ % aliases)
            assert self.ask(space, """
            FFI::AbstractMemory.instance_method(:write_%s) ==
            FFI::AbstractMemory.instance_method(:write_%s)
            """ % aliases)
            assert self.ask(space, """
            FFI::AbstractMemory.instance_method(:read_%s) ==
            FFI::AbstractMemory.instance_method(:read_%s)
            """ % aliases)

    def test_it_defines_long_methods_in_the_following_way(self, space):
        question = """
        FFI::AbstractMemory.instance_method(:PREFIXlong) ==
        FFI::AbstractMemory.instance_method(:PREFIXintSIZEOF_LONG_IN_BITS)
        """.replace('SIZEOF_LONG_IN_BITS', str(8 * rffi.sizeof(rffi.LONG)))
        signed_meths = ['put_', 'get_', 'write_', 'read_']
        unsigned_meths = [meth+'u' for meth in signed_meths]
        for prefix in signed_meths + unsigned_meths:
            assert self.ask(space, question.replace('PREFIX', prefix))

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
