from topaz.modules.ffi.pointer import W_PointerObject
from topaz.modules.ffi.buffer import W_BufferObject
from topaz.module import ClassDef
from topaz.modules.ffi.type import native_types, W_TypeObject, type_object

from rpython.rtyper.lltypesystem import rffi
from rpython.rtyper.lltypesystem import lltype
from rpython.rtyper.lltypesystem.llmemory import (cast_ptr_to_adr as ptr2adr,
                                                  cast_adr_to_int as adr2int)

class W_MemoryPointerObject(W_PointerObject):
    classdef = ClassDef('MemoryPointer', W_PointerObject.classdef)

    def __init__(self, space):
        W_PointerObject.__init__(self, space)
        self.w_type = W_TypeObject(space, 'DUMMY')

    def __del__(self):
        lltype.free(self.ptr, flavor='raw')

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_MemoryPointerObject(space)

    @classdef.method('initialize', size='int')
    def method_initialize(self, space, w_type_hint, size=1):
        self.w_type = type_object(space, w_type_hint)
        sizeof_type = space.int_w(space.send(self.w_type, 'size'))
        self.sizeof_memory = size * sizeof_type
        memory = lltype.malloc(rffi.CArray(rffi.CHAR), self.sizeof_memory,
                               flavor='raw')
        self.ptr = rffi.cast(rffi.VOIDP, memory)
        self.address = adr2int(ptr2adr(self.ptr))
