from topaz.objects.objectobject import W_Object
from topaz.module import ClassDef
from topaz.coerce import Coerce

from rpython.rtyper.lltypesystem import rffi
from rpython.rtyper.lltypesystem import lltype

# Check, whether is will be inlined
def new_cast_method(ctype):
    def cast_method(memory):
        return rffi.cast(lltype.Ptr(rffi.CArray(ctype)), memory.ptr)
    return cast_method

def new_put_method(rffi_type):
    cast_method = new_cast_method(rffi_type)
    sizeof_type = rffi.sizeof(rffi_type)
    def put_method(self, space, offset, value):
        val = rffi.cast(rffi_type, value)
        casted_ptr = cast_method(self)
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

def new_get_method(rffi_type):
    cast_method = new_cast_method(rffi_type)
    sizeof_type = rffi.sizeof(rffi_type)
    def get_method(self, space, offset):
        casted_ptr = cast_method(self)
        try:
            val = casted_ptr[offset]
            if isinstance(val, str):
                return space.newint(ord(val))
            else:
                return space.newint(val)
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

    def __init__(self, space, ptr=rffi.NULL):
        W_Object.__init__(self, space)
        self.ptr = ptr
        self.size = 0

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_AbstractMemoryObject(space)

    char_cast  = new_cast_method(rffi.CHAR)
    short_cast = new_cast_method(rffi.SHORT)
    int_cast   = new_cast_method(rffi.INT)

    def char_size(self):  return self.size
    def short_size(self): return self.size / rffi.sizeof(rffi.SHORT)
    def int_size(self):   return self.size / rffi.sizeof(rffi.INT)

    method_put_int8 = classdef.method('put_int8', offset='int', value='int')(
                      new_put_method(rffi.CHAR))

    method_write_int8 = classdef.method('write_int8')(
                        new_write_method('int8'))

    method_get_int8 = classdef.method('get_int8', offset='int')(
                      new_get_method(rffi.CHAR))

    method_read_int8 = classdef.method('read_int8')(
                      new_read_method('int8'))

    method_put_int32 = classdef.method('put_int32', offset='int', value='int')(
                       new_put_method(rffi.INT))

    method_write_int32 = classdef.method('write_int32')(
                         new_write_method('int32'))

    method_get_int32 = classdef.method('get_int32', offset='int')(
                       new_get_method(rffi.INT))

    method_read_int32 = classdef.method('read_int32')(
                        new_read_method('int32'))

    @classdef.method('put_array_of_int32', begin='int', arr_w='array')
    def method_put_array_of_int32(self, space, begin, arr_w):
        if(begin < 0 or self.int_size() <= begin or
           self.int_size() < begin + len(arr_w)):
            raise memory_index_error(space, begin, 4*len(arr_w))
        for i, w_obj in enumerate(arr_w):
            try:
                someint = Coerce.int(space, w_obj)
                val = rffi.cast(rffi.INT, someint)
                int_ptr = self.int_cast()
                int_ptr[begin + i] = val
            except:
                assert False

    @classdef.method('get_array_of_int32', begin='int', length='int')
    def method_get_array_of_int32(self, space, begin, length):
        arr_w = []
        for i in range(begin, begin + length):
            int_ptr = self.int_cast()
            val = int_ptr[i]
            arr_w.append(space.newint(val))
        return space.newarray(arr_w)
