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

    @classdef.method('method_missing')
    def method_method_missing(self, space, w_meth_id, args_w, block):
        w_meth_name = space.send(w_meth_id, 'id2name')
        meth_name = space.symbol_w(w_meth_name)
        w_buffer = self.find_instance_var(space, '@buffer')
        return space.send(w_buffer, meth_name, args_w, block)

