from topaz.modules.ffi.pointer import W_PointerObject
from topaz.module import ClassDef
from topaz.modules.ffi.type import W_TypeObject, type_object

from rpython.rtyper.lltypesystem import rffi
from rpython.rtyper.lltypesystem import lltype
from rpython.rlib.rbigint import rbigint

class W_MemoryPointerObject(W_PointerObject):
    classdef = ClassDef('MemoryPointer', W_PointerObject.classdef)

    def __init__(self, space):
        W_PointerObject.__init__(self, space)
        self.w_type = None

    def __del__(self):
        lltype.free(self.ptr, flavor='raw')

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_MemoryPointerObject(space)

    @classdef.method('initialize', size='int')
    def method_initialize(self, space, w_type_hint, size=1):
        self.w_type = type_object(space, w_type_hint)
        sizeof_type = space.int_w(space.send(self.w_type, 'size'))
        self.sizeof_memory = rbigint.fromint(size * sizeof_type)
        memory = lltype.malloc(rffi.CArray(rffi.CHAR),
                               self.sizeof_memory.toint(),
                               flavor='raw')
        self.ptr = rffi.cast(rffi.VOIDP, memory)
        self.address = rbigint.fromint(rffi.cast(lltype.Signed, memory))
