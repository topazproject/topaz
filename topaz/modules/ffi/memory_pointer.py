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

    @classdef.method("put_bytes", start='int', string='str', str_offset='int', nbytes='int')
    def method_put_bytes(self, space, start, string, str_offset, nbytes):
        with rffi.scoped_view_charp(string) as cstring:
            rffi.c_memcpy(
                rffi.ptradd(self.ptr, start),
                rffi.cast(rffi.VOIDP, rffi.ptradd(cstring, str_offset)),
                nbytes
            )

    @classdef.method("get_bytes", start='int', nbytes='int')
    def method_get_bytes(self, space, start, nbytes):
        return space.newstr_fromstr(
            rffi.charpsize2str(
                rffi.cast(rffi.CCHARP, rffi.ptradd(self.ptr, start)),
                nbytes
            )
        )

    @classdef.method("get_string", start='int')
    def method_get_string(self, space, start):
        return space.newstr_fromstr(
            rffi.charp2str(rffi.cast(rffi.CCHARP, rffi.ptradd(self.ptr, start)))
        )
