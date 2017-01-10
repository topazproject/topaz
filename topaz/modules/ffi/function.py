import sys

from topaz.module import ClassDef
from topaz.modules.ffi import type as ffitype
from topaz.modules.ffi.pointer import W_PointerObject
from topaz.modules.ffi.dynamic_library import coerce_dl_symbol
from topaz.modules.ffi.function_type import W_FunctionTypeObject
from topaz.objects.moduleobject import W_FunctionObject

from rpython.rtyper.lltypesystem import rffi, lltype
from rpython.rlib import jit
from rpython.rlib.jit_libffi import CIF_DESCRIPTION
from rpython.rlib.jit_libffi import FFI_TYPE_PP

for i, name in enumerate(ffitype.type_names):
    globals()[name] = i

class W_FFIFunctionObject(W_PointerObject):
    classdef = ClassDef('FFI::Function', W_PointerObject.classdef)
    _immutable_fields_ = ['ptr']

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_FFIFunctionObject(space)

    def __init__(self, space):
        W_PointerObject.__init__(self, space)
        self.ptr = lltype.nullptr(rffi.VOIDP.TO)

    @classdef.method('initialize')
    def method_initialize(self, space, w_ret_type, w_arg_types,
                          w_handle=None, w_options=None):
        self.w_info = space.send(space.getclassfor(W_FunctionTypeObject),
                                 'new', [w_ret_type, w_arg_types, w_options])
        self.setup(space, w_handle)

    def setup(self, space, w_handle):
        self.ptr = (coerce_dl_symbol(space, w_handle) if w_handle
                    else lltype.nullptr(rffi.VOIDP.TO))

    @classdef.method('call')
    def method_call(self, space, args_w, block=None):
        return self.w_info.invoke(space, self.ptr, args_w, block)

    @classdef.method('attach', name='str')
    def method_attach(self, space, w_lib, name):
        w_lib.attach_method(space, name, W_MethodAdapter(name, self))

class W_MethodAdapter(W_FunctionObject):
    _immutable_fields_ = ['name', 'w_ffi_func']

    def __init__(self, name, w_ffi_func):
        W_FunctionObject.__init__(self, name)
        self.name = name
        self.w_ffi_func = w_ffi_func

    def call(self, space, w_receiver, args_w, block):
        return space.send(self.w_ffi_func, 'call', args_w, block)
