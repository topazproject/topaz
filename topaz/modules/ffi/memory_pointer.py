from topaz.modules.ffi.pointer import W_PointerObject
from topaz.modules.ffi.buffer import W_BufferObject
from topaz.module import ClassDef
from topaz.modules.ffi.type import type_object

from rpython.rtyper.lltypesystem import rffi

class W_MemoryPointerObject(W_PointerObject):
    classdef = ClassDef('MemoryPointer', W_PointerObject.classdef)

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_MemoryPointerObject(space)


    @classdef.method('initialize', size='int')
    def method_initialize(self, space, w_type_hint, size):
        self.w_type = type_object(space, w_type_hint)
        self.content = [0]*size
