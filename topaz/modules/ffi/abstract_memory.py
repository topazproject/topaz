from topaz.objects.objectobject import W_Object
from topaz.module import ClassDef
from topaz.coerce import Coerce
from topaz.modules.ffi.type import native_types

from rpython.rtyper.lltypesystem import rffi, lltype
from rpython.rlib.rarithmetic import intmask

# Check, whether is will be inlined
def new_cast_method(type_str):
    ctype = native_types[type_str.upper()]
    def cast_method(memory):
        return rffi.cast(lltype.Ptr(rffi.CArray(ctype)), memory.ptr)
    return cast_method

def new_numberof_method(type_str):
    ctype = native_types[type_str.upper()]
    def numberof_method(self):
        return self.sizeof_memory / rffi.sizeof(ctype)
    return numberof_method

def new_put_method(type_str):
    ctype = native_types[type_str.upper()]
    cast_method = new_cast_method(type_str)
    numberof_method = new_numberof_method(type_str)
    sizeof_type = rffi.sizeof(ctype)
    def put_method(self, space, offset, value):
        val = rffi.cast(ctype, value)
        casted_ptr = cast_method(self)
        if offset >= numberof_method(self):
            raise memory_index_error(space, offset, sizeof_type)
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
    ctype = native_types[type_str.upper()]
    cast_method = new_cast_method(type_str)
    numberof_method = new_numberof_method(type_str)
    sizeof_type = rffi.sizeof(ctype)
    if ctype is rffi.CHAR:
        to_int = lambda x: ord(x) - 256 if ord(x) >= 128 else ord(x)
    else:
        to_int = intmask
    def get_method(self, space, offset):
        casted_ptr = cast_method(self)
        if offset >= numberof_method(self):
            raise memory_index_error(space, offset, sizeof_type)
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

def memory_index_error(space, offset, size):
    return space.error(space.w_IndexError,
                       "Memory access offset=%s size=%s is out of bounds"
                       % (offset, size))

class W_AbstractMemoryObject(W_Object):
    classdef = ClassDef('Pointer', W_Object.classdef)

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space):
        return W_AbstractMemoryObject(space)

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
          'uint8', 'uint16', 'uint32']:
    setattr(W_AMO, t + '_cast', new_cast_method(t))
    setattr(W_AMO, t + '_size', new_numberof_method(t))
    setattr(W_AMO, 'method_put_' + t,
            W_AMO.classdef.method('put_' + t, offset='int', value='int')(
            new_put_method(t)))
    setattr(W_AMO, 'method_write_' + t,
            W_AMO.classdef.method('write_' + t, offset='int', value='int')(
            new_write_method(t)))
    setattr(W_AMO, 'method_get_' + t,
            W_AMO.classdef.method('get_' + t, offset='int', value='int')(
            new_get_method(t)))
    setattr(W_AMO, 'method_read_' + t,
            W_AMO.classdef.method('read_' + t, offset='int', value='int')(
            new_read_method(t)))
