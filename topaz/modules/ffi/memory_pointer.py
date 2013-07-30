from topaz.modules.ffi.pointer import W_PointerObject
from topaz.modules.ffi.buffer import W_BufferObject
from topaz.module import ClassDef
from topaz.modules.ffi.type import native_types, W_TypeObject, type_object
from topaz.coerce import Coerce

from rpython.rtyper.lltypesystem import rffi
from rpython.rtyper.lltypesystem import lltype

class W_MemoryPointerObject(W_PointerObject):
    classdef = ClassDef('MemoryPointer', W_PointerObject.classdef)

    def __init__(self, space):
        W_PointerObject.__init__(self, space)
        self.w_type = W_TypeObject(space, 'DUMMY')

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_MemoryPointerObject(space)

    @classdef.method('initialize', size='int')
    def method_initialize(self, space, w_type_hint, size):
        self.w_type = type_object(space, w_type_hint)
        array_type = rffi.CArray(native_types[self.w_type.name])
        self.ptr = lltype.malloc(array_type, size, flavor='raw')
        self._size = size

    @classdef.method('put_array_of_int32', begin='int', arr_w='array')
    def method_put_array_of_int32(self, space, begin, arr_w):
        if(begin < 0 or self._size <= begin or
           self._size < begin + len(arr_w)):
            errmsg = ("Memory access offset=%s size=%s is out of bounds"
                      % (begin, 4*len(arr_w)))
            raise space.error(space.w_IndexError, errmsg)
        for i, w_obj in enumerate(arr_w):
            try:
                someint = Coerce.int(space, w_obj)
                val = rffi.cast(rffi.INT, someint)
                self.ptr[begin + i] = val
            except:
                assert False

    @classdef.method('get_array_of_int32', begin='int', length='int')
    def method_get_array_of_int32(self, space, begin, length):
        #arr = self.content[begin : begin + length]
        arr_w = []
        for i in range(begin, begin + length):
            val = self.ptr[i]
            arr_w.append(space.newint(val))
        return space.newarray(arr_w)
