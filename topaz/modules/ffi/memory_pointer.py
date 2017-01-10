from topaz.modules.ffi.pointer import W_PointerObject
from topaz.module import ClassDef
from topaz.modules.ffi.type import W_TypeObject

from rpython.rtyper.lltypesystem import rffi
from rpython.rtyper.lltypesystem import lltype

class W_MemoryPointerObject(W_PointerObject):
    classdef = ClassDef('FFI::MemoryPointer', W_PointerObject.classdef)

    def __init__(self, space):
        W_PointerObject.__init__(self, space)
        self.w_type = None

    def __del__(self):
        lltype.free(self.ptr, flavor='raw')

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_MemoryPointerObject(space)

    @classdef.method('initialize', type_hint='symbol', size='int')
    def method_initialize(self, space, type_hint, size=1):
        w_FFI = space.find_const(space.w_kernel, 'FFI')
        w_Type = space.find_const(w_FFI, 'Type')
        self.w_type = space.find_const(w_Type, type_hint.upper())
        sizeof_type = space.int_w(space.send(self.w_type, 'size'))
        self.sizeof_memory = size * sizeof_type
        memory = lltype.malloc(rffi.CArray(rffi.CHAR),
                               self.sizeof_memory,
                               flavor='raw', zero=True)
        self.ptr = rffi.cast(rffi.VOIDP, memory)
