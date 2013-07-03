from topaz.modules.ffi.pointer import W_PointerObject
from topaz.modules.ffi.buffer import W_BufferObject
from topaz.module import ClassDef

from rpython.rtyper.lltypesystem import rffi

class W_MemoryPointerObject(W_PointerObject):
    classdef = ClassDef('MemoryPointer', W_PointerObject.classdef)

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_MemoryPointerObject(space)

    @classdef.method('initialize')
    def method_initialize(self, space, w_sym):
        w_buffer_cls = space.getclassfor(W_BufferObject)
        w_buffer = space.send(w_buffer_cls, 'new', [w_sym])
        self.set_instance_var(space, '@buffer', w_buffer)
