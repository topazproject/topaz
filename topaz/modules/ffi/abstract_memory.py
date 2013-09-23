from topaz.objects.objectobject import W_Object
from topaz.module import ClassDef
from topaz.coerce import Coerce
from topaz.modules.ffi.type import lltype_for_name, lltypes, UINT64, lltype_sizes 
from rpython.rtyper.lltypesystem import rffi, lltype
from rpython.rtyper.lltypesystem.llmemory import (cast_ptr_to_adr as ptr2adr,
                                                  cast_adr_to_int as adr2int)
from rpython.rlib.rarithmetic import intmask
from rpython.rlib.rbigint import rbigint

# Check, whether is will be inlined
def new_cast_method(type_str):
    ctype = lltype_for_name(type_str.upper())
    def cast_method(memory):
        return rffi.cast(lltype.Ptr(rffi.CArray(ctype)), memory.ptr)
    return cast_method

def new_numberof_method(type_str):
    ctype = lltype_for_name(type_str.upper())
    def numberof_method(self):
        return self.sizeof_memory.toulonglong() / rffi.sizeof(ctype)
    return numberof_method

def new_put_method(type_str):
    ctype = lltype_for_name(type_str.upper())
    cast_method = new_cast_method(type_str)
    numberof_method = new_numberof_method(type_str)
    sizeof_type = rffi.sizeof(ctype)
    def put_method(self, space, offset, value):
        val = rffi.cast(ctype, value)
        casted_ptr = cast_method(self)
        raise_if_out_of_bounds(space, offset, numberof_method(self),
                               memory_index_error(space, offset, sizeof_type))
        try:
            casted_ptr[offset] = val
        except IndexError:
            raise memory_index_error(space, offset, sizeof_type)
    return put_method

def new_write_method(type_str):
    put_method_name = 'put_' + type_str
    def write_method(self, space, w_value):
        space.send(self, put_method_name, [space.newint(0), w_value])
    return write_method

def new_get_method(type_str):
    ctype = lltype_for_name(type_str.upper())
    cast_method = new_cast_method(type_str)
    numberof_method = new_numberof_method(type_str)
    sizeof_type = rffi.sizeof(ctype)
    if type_str == 'int8':
        to_int = lambda x: ord(x) - 256 if ord(x) >= 128 else ord(x)
    else:
        to_int = intmask
    def get_method(self, space, offset):
        casted_ptr = cast_method(self)
        raise_if_out_of_bounds(space, offset, numberof_method(self),
                               memory_index_error(space, offset, sizeof_type))
        try:
            val = casted_ptr[offset]
            return space.newint(to_int(val))
        except IndexError:
            raise memory_index_error(space, offset, sizeof_type)
    return get_method

def new_read_method(type_str):
    get_method_name = 'get_' + type_str
    def read_method(self, space):
        return space.send(self, get_method_name, [space.newint(0)])
    return read_method

def raise_if_out_of_bounds(space, offset, size, error):
    if offset < 0:
        raise error
    else:
        if offset >= size:
            raise error

def memory_index_error(space, offset, size):
    return space.error(space.w_IndexError,
                       "Memory access offset=%s size=%s is out of bounds"
                       % (offset, size))

class W_AbstractMemoryObject(W_Object):
    classdef = ClassDef('Pointer', W_Object.classdef)

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space):
        return W_AbstractMemoryObject(space)

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        for orig, alias in [
                            ('int8', 'char'),
                            ('uint8', 'uchar'),
                            ('int16', 'short'),
                            ('uint16', 'ushort'),
                            ('int32', 'int'),
                            ('uint32', 'uint')
                           ]:
            for prefix in ['put_', 'get_', 'write_', 'read_']:
                space.send(w_cls, 'alias_method',
                           [space.newsymbol(prefix + alias),
                            space.newsymbol(prefix + orig)])

    @classdef.method('put_pointer', offset='int', value='ffi_address')
    def method_put_pointer(self, space, offset, value):
        like_ptr = lltypes[UINT64]
        sizeof_type = lltype_sizes[UINT64]
        val = rffi.cast(like_ptr, value.toulonglong())
        casted_ptr = self.uint64_cast()
        raise_if_out_of_bounds(space, offset, self.uint64_size(),
                               memory_index_error(space, offset, sizeof_type))
        try:
            casted_ptr[offset] = val
        except IndexError:
            raise memory_index_error(space, offset, sizeof_type)

    @classdef.method('get_pointer', offset='int')
    def method_get_pointer(self, space, offset):
        like_ptr = lltypes[UINT64]
        sizeof_type = lltype_sizes[UINT64]
        casted_ptr = self.uint64_cast()
        raise_if_out_of_bounds(space, offset, self.uint64_size(),
                               memory_index_error(space, offset, sizeof_type))
        try:
            address = casted_ptr[offset]
            rbigint_address = rbigint.fromrarith_int(address)
            w_address = space.newbigint_fromrbigint(rbigint_address)
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
for t in ['int8', 'int16', 'int32', 'int64',
          'uint8', 'uint16', 'uint32', 'uint64']:
    setattr(W_AMO, t + '_cast', new_cast_method(t))
    setattr(W_AMO, t + '_size', new_numberof_method(t))
    setattr(W_AMO, 'method_put_' + t,
            W_AMO.classdef.method('put_' + t, offset='int', value='int')(
            new_put_method(t)))
    setattr(W_AMO, 'method_write_' + t,
            W_AMO.classdef.method('write_' + t, value='int')(
            new_write_method(t)))
    setattr(W_AMO, 'method_get_' + t,
            W_AMO.classdef.method('get_' + t, offset='int')(
            new_get_method(t)))
    setattr(W_AMO, 'method_read_' + t,
            W_AMO.classdef.method('read_' + t)(
            new_read_method(t)))
