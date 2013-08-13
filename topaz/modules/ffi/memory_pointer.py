from topaz.modules.ffi.pointer import W_PointerObject
from topaz.modules.ffi.buffer import W_BufferObject
from topaz.module import ClassDef
from topaz.modules.ffi.type import native_types, W_TypeObject, type_object

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
        array_type = lltype.GcArray(native_types[self.w_type.name])
        self.ptr = lltype.malloc(array_type, size)
        self.size = size * space.int_w(space.send(self.w_type, 'size'))
