from tests.modules.ffi.base import BaseFFITest
from topaz.modules.ffi import type as ffitype

from rpython.rtyper.lltypesystem import rffi

from pypy.module._cffi_backend import misc

import sys
import pytest

test_types = [ffitype.INT8, ffitype.INT16, ffitype.INT32, ffitype.INT64,
              ffitype.UINT8, ffitype.UINT16, ffitype.UINT32, ffitype.UINT64,
              ffitype.FLOAT32, ffitype.FLOAT64]

read = {}
for t in [ffitype.INT8, ffitype.INT16, ffitype.INT32, ffitype.INT64]:
    read[t] = misc.read_raw_signed_data
for t in [ffitype.UINT8, ffitype.UINT16, ffitype.UINT32, ffitype.UINT64]:
    read[t] = misc.read_raw_unsigned_data
for t in [ffitype.FLOAT32, ffitype.FLOAT64]:
    read[t] = misc.read_raw_float_data

minval = {}
maxval = {}
for bits in [8, 16, 32, 64]:
    minval['int' + str(bits)] = int(-2**(bits-1))
    minval['uint' + str(bits)] = 0
    maxval['int' + str(bits)] = int(2**(bits-1) - 1)
    # for some reason int(2**64 -1) is not accepted as biggest uint64
    maxval['uint' + str(bits)] = int(2**(bits-1) - 1)
minval['long'] = int(-2**(8*rffi.sizeof(rffi.LONG)))
minval['ulong'] = 0
maxval['long'] = int(2**(8*rffi.sizeof(rffi.LONG)) - 1)
maxval['ulong'] = int(2**(8*rffi.sizeof(rffi.LONG)-1) - 1)
minval['float32'] = 1.1754943508222875e-38
maxval['float32'] = 3.4028234663852886e+38
minval['float64'] = sys.float_info.min
maxval['float64'] = sys.float_info.max

def new_cast_method(typ):
    ctype = ffitype.lltypes[typ]
    def cast_method(memory):
        return rffi.cast(ffitype.lltype.Ptr(rffi.CArray(ctype)), memory.ptr)
    return cast_method

def new_numberof_method(typ):
    csize = ffitype.lltype_sizes[typ]
    if csize & (csize - 1) == 0:  # csize is a power of 2
        shift = 0
        while 1 << shift < csize: shift += 1
        def numberof_method(self):
            return self.sizeof_memory >> shift
    else:
        def numberof_method(self):
            return self.sizeof_memory / csize
    return numberof_method

def put_method_test_code(typename):
    # For some reason, str(some_float) cuts off a few digits.
    # Only repr prints the entire float.
    strfunc = ((lambda x: repr(x)) if 'float' in typename else
               (lambda x: str(x)))
    return ("""
    mem_ptr = FFI::MemoryPointer.new(:TYPE, 2)
    mem_ptr.put_TYPE(0, MIN)
    mem_ptr.put_TYPE(FFI::Type::UPPER.size, MAX)
    mem_ptr
    """.replace('TYPE', typename).
        replace('UPPER', typename.upper()).
        replace('MIN', strfunc(minval[typename])).
        replace('MAX', strfunc(maxval[typename])))

def get_method_test_code(typename):
    strfunc = ((lambda x: repr(x)) if 'float' in typename else
               (lambda x: str(x)))
    return ("""
    mem_ptr = FFI::MemoryPointer.new(:TYPE, 5)
    pos_3 = FFI::Type::UPPER.size * 3
    pos_4 = FFI::Type::UPPER.size * 4
    mem_ptr.put_TYPE(pos_3, MIN)
    mem_ptr.put_TYPE(pos_4, MAX)
    [mem_ptr.get_TYPE(pos_3), mem_ptr.get_TYPE(pos_4)]
    """.replace('TYPE', typename).
        replace('UPPER', typename.upper()).
        replace('MIN', strfunc(minval[typename])).
        replace('MAX', strfunc(maxval[typename])))

class TestAbstractMemory_put_methods(BaseFFITest):
    def test_they_put_a_single_value_into_the_given_offset(self, space):
        for t in test_types:
            tn = ffitype.type_names[t].lower()
            size = ffitype.lltype_sizes[t]
            w_mem_ptr = space.execute(put_method_test_code(tn))
            expected_0 = minval[tn]
            expected_1 = maxval[tn]
            ptr_0 = w_mem_ptr.ptr
            ptr_1 = rffi.ptradd(ptr_0, size)
            actual_0 = read[t](ptr_0, size)
            actual_1 = read[t](ptr_1, size)
            assert expected_0 == actual_0
            assert expected_1 == actual_1

    def test_they_refuse_negative_offsets(self, space):
        for t in test_types:
            tn = ffitype.type_names[t]
            sizeof_t = ffitype.lltype_sizes[t]
            with self.raises(space, 'IndexError',
                             "Memory access offset=-1 size=%s is out of bounds"
                             %  sizeof_t):
                space.execute("""
                FFI::MemoryPointer.new(:T, 1).put_T(-1, 230)
                """.replace('T', tn.lower()))

    def test_they_refuse_too_large_offsets(self, space):
        for t in test_types:
            tn = ffitype.type_names[t]
            sizeof_t = ffitype.lltype_sizes[t]
            with self.raises(space, 'IndexError',
                             "Memory access offset=1000 size=%s is out of bounds"
                             % sizeof_t):
                space.execute("""
                FFI::MemoryPointer.new(:T, 3).put_T(1000, 15)
                """.replace('T', tn.lower()))

class TestAbstractMemory_write_methods(BaseFFITest):
    def test_they_are_like_calling_put_with_0_as_1st_arg(self, space):
        for t in test_types:
            tn = ffitype.type_names[t]
            w_mem_ptr = space.execute("""
            mem_ptr = FFI::MemoryPointer.new(:T, 1)
            mem_ptr.write_T(121)
            mem_ptr
            """.replace('T', tn.lower()))
            cast_method = new_cast_method(t)
            casted_ptr = cast_method(w_mem_ptr)
            assert casted_ptr[0] == 'y' if tn == 'INT8' else 121

class TestAbstractMemory_get_methods(BaseFFITest):
    def test_they_get_a_single_value_from_the_given_offset(self, space):
        for tn in [ffitype.type_names[t].lower()
                   for t in test_types]:
            w_res = space.execute(get_method_test_code(tn))
            assert self.unwrap(space, w_res) == [minval[tn], maxval[tn]]

class TestAbstractMemory_read_methods(BaseFFITest):
    def test_they_are_like_calling_get_with_0(self, space):
        for tn in [ffitype.type_names[t].lower()
                  for t in test_types]:
            w_res = space.execute("""
            mem_ptr = FFI::MemoryPointer.new(:T, 1)
            mem_ptr.write_T(1)
            mem_ptr.read_T
            """.replace('T', tn))
            assert self.unwrap(space, w_res) == 1

class TestAbstractMemory_put_pointer(BaseFFITest):
    def test_it_puts_a_single_pointer_into_the_given_offset(self, space):
        w_mem_ptr = space.execute("""
        mem_ptr = FFI::MemoryPointer.new(:pointer, 2)
        ptr1 = FFI::Pointer.new(88)
        ptr2 = FFI::Pointer.new(55)
        mem_ptr.put_pointer(0, ptr1)
        mem_ptr.put_pointer(FFI::Type::POINTER.size, ptr2)
        mem_ptr
        """)
        w_adr_ptr = new_cast_method(ffitype.UINT64)(w_mem_ptr)
        assert w_adr_ptr[0] == 88
        assert w_adr_ptr[1] == 55

class TestAbstractMemory_get_pointer(BaseFFITest):
    def test_it_gets_a_single_pointer_from_the_given_offset(self, space):
        assert self.ask(space, """
        mem_ptr = FFI::MemoryPointer.new(:pointer, 4)
        pos_3 = FFI::Type::POINTER.size * 3
        mem_ptr.put_pointer(pos_3, FFI::Pointer.new(67))
        ptr = mem_ptr.get_pointer(pos_3)
        ptr.class.equal?(FFI::Pointer) and ptr.address == 67
        """)

    def test_it_always_returns_a_simple_pointer(self, space):
        assert self.ask(space, """
        outer_mem_ptr = FFI::MemoryPointer.new(:pointer, 1)
        inner_mem_ptr = FFI::MemoryPointer.new(:int8, 1)
        outer_mem_ptr.put_pointer(0, inner_mem_ptr)
        ! outer_mem_ptr.get_pointer(0).class.equal? FFI::MemoryPointer
        outer_mem_ptr.get_pointer(0).class.equal? FFI::Pointer
        """)

    def test_it_doesnt_loose_the_content(self, space):
        w_res = space.execute("""
        outer_mem_ptr = FFI::MemoryPointer.new(:pointer, 1)
        inner_mem_ptr = FFI::MemoryPointer.new(:int16, 1)
        inner_mem_ptr.write_int16(300)
        outer_mem_ptr.put_pointer(0, inner_mem_ptr)
        outer_mem_ptr.get_pointer(0).read_int16
        """)
        assert self.unwrap(space, w_res) == 300

class TestAbstractMemory_write_pointer(BaseFFITest):
    def test_it_is_like_calling_put_pointer_with_0_as_1st_arg(self, space):
        w_res = space.execute("""
        mem_ptr = FFI::MemoryPointer.new(:pointer, 1)
        mem_ptr.write_pointer(FFI::Pointer.new(11))
        mem_ptr.get_pointer(0).address
        """)
        assert self.unwrap(space, w_res) == 11

class TestAbstractMemory_write_uint64(BaseFFITest):
    def test_it_is_like_calling_put_uint64_with_0_as_1st_arg(self, space):
        w_res = space.execute("""
        mem_ptr = FFI::MemoryPointer.new(:uint64, 1)
        mem_ptr.write_uint64(14)
        mem_ptr.get_uint64(0)
        """)
        assert self.unwrap(space, w_res) == 14

class TestAbstractMemory_read_pointer(BaseFFITest):
    def test_it_is_like_calling_get_pointer_with_0(self, space):
        w_res = space.execute("""
        mem_ptr = FFI::MemoryPointer.new(:pointer, 1)
        mem_ptr.put_pointer(0, FFI::Pointer.new(13))
        mem_ptr.read_pointer.address
        """)
        assert self.unwrap(space, w_res) == 13

class TestAbstractMemory_read_uint64(BaseFFITest):
    def test_it_is_like_calling_get_uint64_with_0(self, space):
        w_res = space.execute("""
        mem_ptr = FFI::MemoryPointer.new(:uint64, 1)
        mem_ptr.put_uint64(0, 12)
        mem_ptr.read_uint64
        """)
        assert self.unwrap(space, w_res) == 12

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
#    def test_it_writes_into_array(self, space):
#        w_mem_ptr = space.execute("""
#        mem_ptr = FFI::MemoryPointer.new(:int32, 10)
#        mem_ptr.put_array_of_int32(0, (0..9).to_a)
#        mem_ptr
#        """)
#        int_ptr = w_mem_ptr.int32_cast()
#        for i in range(10):
#            assert int_ptr[i] == i
#
#    def test_it_refuses_negative_offset(self, space):
#        with self.raises(space, 'IndexError',
#                         "Memory access offset=-1 size=4 is out of bounds"):
#            space.execute("""
#            mem_ptr = FFI::MemoryPointer.new(:int32, 1)
#            mem_ptr.put_array_of_int32(-1, [0])
#            """)
#
#    def test_it_refuses_too_large_offset(self, space):
#        with self.raises(space, 'IndexError',
#                         "Memory access offset=3 size=4 is out of bounds"):
#            w_mem_ptr = space.execute("""
#            mem_ptr = FFI::MemoryPointer.new(:int32, 3)
#            mem_ptr.put_array_of_int32(3, [13])
#            """)
#
#    def test_it_refuses_too_large_offset_even_without_writing(self, space):
#        with self.raises(space, 'IndexError',
#                         "Memory access offset=5 size=0 is out of bounds"):
#            w_mem_ptr = space.execute("""
#            mem_ptr = FFI::MemoryPointer.new(:int32, 5)
#            mem_ptr.put_array_of_int32(5, [])
#            """)
#
#    def test_it_refuses_too_big_array(self, space):
#        with self.raises(space, 'IndexError',
#                         "Memory access offset=0 size=12 is out of bounds"):
#            w_mem_ptr = space.execute("""
#            mem_ptr = FFI::MemoryPointer.new(:int32, 2)
#            mem_ptr.put_array_of_int32(0, [1, 2, 3])
#            """)
#
#class TestAbstractMemory__get_array_of_int32(BaseFFITest):
#    def test_it_reads_from_array(self, space):
#        w_res = space.execute("""
#        mem_ptr = FFI::MemoryPointer.new(:int32, 10)
#        mem_ptr.put_array_of_int32(0, (0..9).to_a)
#        mem_ptr.get_array_of_int32(0, 10)
#        """)
#        assert self.unwrap(space, w_res) == range(10)
