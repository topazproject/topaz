from topaz.modules.ffi.pointer import W_PointerObject
from topaz.modules.ffi.buffer import W_BufferObject
from topaz.module import ClassDef
from topaz.modules.ffi.type import W_TypeObject, type_object
from topaz.coerce import Coerce

from rpython.rtyper.lltypesystem import rffi

class W_MemoryPointerObject(W_PointerObject):
    classdef = ClassDef('MemoryPointer', W_PointerObject.classdef)

    def __init__(self, space):
        W_PointerObject.__init__(self, space)
        self.w_type = W_TypeObject(space, 'DUMMY')
        self.content = []

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_MemoryPointerObject(space)


    @classdef.method('initialize', size='int')
    def method_initialize(self, space, w_type_hint, size):
        self.w_type = type_object(space, w_type_hint)
        self.content = [0]*size

    @classdef.method('put_array_of_int32', begin='int', arr_w='array')
    def method_put_array_of_int32(self, space, begin, arr_w):
        for i, w_obj in enumerate(arr_w):
            try:
                someint = Coerce.int(space, w_obj)
                val = rffi.cast(rffi.INT, someint)
                self.content[begin + i] = val
            except:
                assert False
