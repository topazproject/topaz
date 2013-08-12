from topaz.objects.objectobject import W_Object
from topaz.module import ClassDef
from topaz.coerce import Coerce

from rpython.rtyper.lltypesystem import rffi

class W_AbstractMemoryObject(W_Object):
    classdef = ClassDef('Pointer', W_Object.classdef)

    def __init__(self, space, ptr=rffi.NULL):
        W_Object.__init__(self, space)
        self.ptr = ptr
        self._size = 0

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_AbstractMemoryObject(space)

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
        arr_w = []
        for i in range(begin, begin + length):
            val = self.ptr[i]
            arr_w.append(space.newint(val))
        return space.newarray(arr_w)
