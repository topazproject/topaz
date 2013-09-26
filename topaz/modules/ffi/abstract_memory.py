from topaz.objects.objectobject import W_Object
from topaz.module import ClassDef
from topaz.coerce import Coerce
from topaz.modules.ffi.type import lltype_for_name, lltypes, UINT64, lltype_sizes
from rpython.rtyper.lltypesystem import rffi, lltype
from rpython.rlib.rarithmetic import intmask, r_longlong, r_ulonglong
from rpython.rlib.rbigint import rbigint

from topaz.modules.ffi import type as ffitype

import sys

# Check, whether this will be inlined
def new_cast_method(typ):
    ctype = ffitype.lltypes[typ]
    def cast_method(memory):
        return rffi.cast(lltype.Ptr(rffi.CArray(ctype)), memory.ptr)
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

def new_put_method(typ):
    ctype = ffitype.lltypes[typ]
    cast_method = new_cast_method(typ)
    numberof_method = new_numberof_method(typ)
    sizeof_type  = ffitype.lltype_sizes[typ]
    def put_method(self, space, offset, value):
        val = rffi.cast(ctype, value)
        casted_ptr = cast_method(self)
        raise_if_out_of_bounds(space, offset, numberof_method(self), sizeof_type)
        try:
            casted_ptr[offset] = val
        except IndexError:
            raise memory_index_error(space, offset, sizeof_type)
    return put_method

def new_get_method(typ):
    ctype = ffitype.lltypes[typ]
    cast_method = new_cast_method(typ)
    numberof_method = new_numberof_method(typ)
    sizeof_type  = ffitype.lltype_sizes[typ]
    if typ == ffitype.INT8:
        to_int = lambda x: ord(x) - 256 if ord(x) >= 128 else ord(x)
    else:
        to_int = intmask
    if typ in [ffitype.FLOAT32, ffitype.FLOAT64]:
        wrap = lambda space, val: space.newfloat(float(val))
    else:
        wrap = lambda space, val: space.newint(to_int(val))
    def get_method(self, space, offset):
        casted_ptr = cast_method(self)
        raise_if_out_of_bounds(space, offset, numberof_method(self), sizeof_type)
        try:
            val = casted_ptr[offset]
            return wrap(space, val)
        except IndexError:
            raise memory_index_error(space, offset, sizeof_type)
    return get_method

def new_write_method(type_str):
    put_method_name = 'put_' + type_str
    def write_method(self, space, w_value):
        space.send(self, put_method_name, [space.newint(0), w_value])
    return write_method

def new_read_method(type_str):
    get_method_name = 'get_' + type_str
    def read_method(self, space):
        return space.send(self, get_method_name, [space.newint(0)])
    return read_method

def raise_if_out_of_bounds(space, offset, size, sizeof_type):
    if offset < 0:
        raise memory_index_error(space, offset, sizeof_type)
    else:
        if offset >= size:
            raise memory_index_error(space, offset, sizeof_type)

def memory_index_error(space, offset, size):
    return space.error(space.w_IndexError,
                       "Memory access offset=%s size=%s is out of bounds"
                       % (offset, size))

class W_AbstractMemoryObject(W_Object):
    classdef = ClassDef('Pointer', W_Object.classdef)
    ptr = lltype.nullptr(rffi.VOIDP.TO)
    _immutable_fields_ = ['ptr']

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space):
        return W_AbstractMemoryObject(space)

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        long_in_bits = 8 * rffi.sizeof(rffi.LONG)
        for orig, alias in [
                            ('int8', 'char'),
                            ('uint8', 'uchar'),
                            ('int16', 'short'),
                            ('uint16', 'ushort'),
                            ('int32', 'int'),
                            ('uint32', 'uint'),
                            ('int64', 'long_long'),
                            ('uint64', 'ulong_long'),
                            ('float32', 'float'),
                            ('float64', 'double'),
                            ('int' + str(long_in_bits), 'long'),
                            ('uint' + str(long_in_bits), 'ulong')
                           ]:
            for prefix in ['put_', 'get_', 'write_', 'read_']:
                space.send(w_cls, 'alias_method',
                           [space.newsymbol(prefix + alias),
                            space.newsymbol(prefix + orig)])

    @classdef.method('put_uint64', offset='int', value='bigint')
    def method_put_uint64(self, space, offset, value):
        like_ptr = lltypes[UINT64]
        sizeof_type = lltype_sizes[UINT64]
        val = rffi.cast(like_ptr, value.toulonglong())
        casted_ptr = self.uint64_cast()
        raise_if_out_of_bounds(space, offset, self.uint64_size(), sizeof_type)
        try:
            casted_ptr[offset] = val
        except IndexError:
            raise memory_index_error(space, offset, sizeof_type)

    @classdef.method('get_uint64', offset='int')
    def method_get_uint64(self, space, offset):
        like_ptr = lltypes[UINT64]
        sizeof_type = lltype_sizes[UINT64]
        casted_ptr = self.uint64_cast()
        raise_if_out_of_bounds(space, offset, self.uint64_size(), sizeof_type)
        try:
            val = casted_ptr[offset]
            return space.newint_or_bigint_fromunsigned(val)
        except IndexError:
            raise memory_index_error(space, offset, sizeof_type)

    method_write_uint64 = classdef.method('write_uint64')(
                           new_write_method('uint64'))

    method_read_uint64 = classdef.method('read_uint64')(
                          new_read_method('uint64'))

    @classdef.method('put_pointer', offset='int', value='ffi_address')
    def method_put_pointer(self, space, offset, value):
        like_ptr = lltypes[UINT64]
        sizeof_type = lltype_sizes[UINT64]
        val = rffi.cast(like_ptr, value)
        casted_ptr = self.uint64_cast()
        raise_if_out_of_bounds(space, offset, self.uint64_size(), sizeof_type)
        try:
            casted_ptr[offset] = val
        except IndexError:
            raise memory_index_error(space, offset, sizeof_type)

    @classdef.method('get_pointer', offset='int')
    def method_get_pointer(self, space, offset):
        like_ptr = lltypes[UINT64]
        sizeof_type = lltype_sizes[UINT64]
        casted_ptr = self.uint64_cast()
        raise_if_out_of_bounds(space, offset, self.uint64_size(), sizeof_type)
        try:
            address = casted_ptr[offset]
            w_address = space.newint_or_bigint(intmask(address))
            w_ffi = space.find_const(space.w_kernel, 'FFI')
            w_pointer = space.find_const(w_ffi, 'Pointer')
            return space.send(w_pointer, 'new', [w_address])
        except IndexError:
            raise memory_index_error(space, offset, sizeof_type)

    method_write_pointer = classdef.method('write_pointer')(
                           new_write_method('pointer'))

    method_read_pointer = classdef.method('read_pointer')(
                          new_read_method('pointer'))

    #@classdef.method('put_array_of_int32', begin='int', arr_w='array')
    #def method_put_array_of_int32(self, space, begin, arr_w):
    #    if(begin < 0 or self.int_size() <= begin or
    #       self.int_size() < begin + len(arr_w)):
    #        raise memory_index_error(space, begin, 4*len(arr_w))
    #    for i, w_obj in enumerate(arr_w):
    #        try:
    #            someint = Coerce.int(space, w_obj)
    #            val = rffi.cast(rffi.SIGNED, someint)
    #            int_ptr = self.int_cast()
    #            int_ptr[begin + i] = val
    #        except:
    #            assert False

    #@classdef.method('get_array_of_int32', begin='int', length='int')
    #def method_get_array_of_int32(self, space, begin, length):
    #    arr_w = []
    #    for i in range(begin, begin + length):
    #        int_ptr = self.int_cast()
    #        val = int_ptr[i]
    #        arr_w.append(space.newint(val))
    #    return space.newarray(arr_w)

W_AMO = W_AbstractMemoryObject
for t in [ffitype.INT8, ffitype.INT16, ffitype.INT32, ffitype.INT64,
         ffitype.UINT8, ffitype.UINT16, ffitype.UINT32, ffitype.UINT64,
         ffitype.FLOAT32, ffitype.FLOAT64]:
    tn = ffitype.type_names[t].lower()
    setattr(W_AMO, tn + '_cast', new_cast_method(t))
    setattr(W_AMO, tn + '_size', new_numberof_method(t))

for t in [ffitype.INT8, ffitype.INT16, ffitype.INT32, ffitype.INT64,
          ffitype.UINT8, ffitype.UINT16, ffitype.UINT32]:
    tn = ffitype.type_names[t].lower()
    setattr(W_AMO, 'method_put_' + tn,
            W_AMO.classdef.method('put_' + tn, offset='int', value='int')(
            new_put_method(t)))
    setattr(W_AMO, 'method_write_' + tn,
            W_AMO.classdef.method('write_' + tn, value='int')(
            new_write_method(tn)))
    setattr(W_AMO, 'method_get_' + tn,
            W_AMO.classdef.method('get_' + tn, offset='int')(
            new_get_method(t)))
    setattr(W_AMO, 'method_read_' + tn,
            W_AMO.classdef.method('read_' + tn)(
            new_read_method(tn)))
for t in [ffitype.FLOAT32, ffitype.FLOAT64]:
    tn = ffitype.type_names[t].lower()
    setattr(W_AMO, 'method_put_' + tn,
            W_AMO.classdef.method('put_' + tn, offset='int', value='float')(
            new_put_method(t)))
    setattr(W_AMO, 'method_write_' + tn,
            W_AMO.classdef.method('write_' + tn, value='float')(
            new_write_method(tn)))
    setattr(W_AMO, 'method_get_' + tn,
            W_AMO.classdef.method('get_' + tn, offset='int')(
            new_get_method(t)))
    setattr(W_AMO, 'method_read_' + tn,
            W_AMO.classdef.method('read_' + tn)(
            new_read_method(tn)))
