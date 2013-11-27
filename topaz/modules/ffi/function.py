import sys

from topaz.module import ClassDef
from topaz.modules.ffi import type as ffitype
from topaz.modules.ffi.type import W_TypeObject, W_MappedObject
from topaz.modules.ffi.pointer import W_PointerObject
from topaz.modules.ffi.dynamic_library import coerce_dl_symbol
from topaz.modules.ffi._memory_access import (read_and_wrap_from_address,
                                              unwrap_and_write_to_address)
from topaz.modules.ffi.function_type import W_FunctionTypeObject
from topaz.modules.ffi import _callback
from topaz.error import RubyError
from topaz.objects.moduleobject import W_FunctionObject

from rpython.rtyper.lltypesystem import rffi, lltype
from rpython.rlib import jit
from rpython.rlib.jit_libffi import CIF_DESCRIPTION
from rpython.rlib.jit_libffi import FFI_TYPE_PP
from rpython.rlib.jit_libffi import jit_ffi_call

# XXX maybe move to rlib/jit_libffi
from pypy.module._cffi_backend import misc

for i, name in enumerate(ffitype.type_names):
    globals()[name] = i

class W_FFIFunctionObject(W_PointerObject):
    classdef = ClassDef('Function', W_PointerObject.classdef)
    _immutable_fields_ = ['cif_descr', 'atypes', 'ptr', 'arg_types_w', 'w_ret_type']

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_FFIFunctionObject(space)

    def __init__(self, space):
        W_PointerObject.__init__(self, space)
        self.w_ret_type = None
        self.arg_types_w = []
        self.ptr = lltype.nullptr(rffi.VOIDP.TO)
        #
        self.cif_descr = lltype.nullptr(CIF_DESCRIPTION)
        self.atypes = lltype.nullptr(FFI_TYPE_PP.TO)

    @classdef.method('initialize')
    def method_initialize(self, space, w_ret_type, w_arg_types,
                          w_handle=None, w_options=None):
        self.w_info = space.send(space.getclassfor(W_FunctionTypeObject),
                                 'new', [w_ret_type, w_arg_types, w_options])
        self.setup(space, w_handle)

    def setup(self, space, w_handle):
        self.ptr = (coerce_dl_symbol(space, w_handle) if w_handle
                    else lltype.nullptr(rffi.VOIDP.TO))
        self.cif_descr = self.w_info.build_cif_descr(space)
        self.atypes = self.cif_descr.atypes

    def initialize_variadic(self, space, w_handle, w_ret_type, arg_types_w):
        self.w_info = space.send(space.getclassfor(W_FunctionTypeObject),
                                 'new',
                                 [w_ret_type, space.newarray(arg_types_w)])
        self.setup(space, w_handle)

    def __del__(self):
        if self.cif_descr:
            lltype.free(self.cif_descr, flavor='raw')
        if self.atypes:
            lltype.free(self.atypes, flavor='raw')


    #XXX eventually we need a dont look inside for vararg calls
    @classdef.method('call')
    @jit.unroll_safe
    def method_call(self, space, args_w, block=None):
        self = jit.promote(self)
        cif_descr = self.cif_descr

        if block is not None:
            args_w.append(block)
        nargs = len(args_w)
        assert nargs == cif_descr.nargs
        #
        size = cif_descr.exchange_size
        buffer = lltype.malloc(rffi.CCHARP.TO, size, flavor='raw')
        try:
            for i in range(len(args_w)):
                data = rffi.ptradd(buffer, cif_descr.exchange_args[i])
                w_obj = args_w[i]
                self._put_arg(space, data, i, w_obj)

            #ec = cerrno.get_errno_container(space)
            #cerrno.restore_errno_from(ec)
            jit_ffi_call(cif_descr, rffi.cast(rffi.VOIDP, self.ptr), buffer)
            #e = cerrno.get_real_errno()
            #cerrno.save_errno_into(ec, e)

            resultdata = rffi.ptradd(buffer, cif_descr.exchange_result)
            w_res =  self._get_result(space, resultdata)
        finally:
            lltype.free(buffer, flavor='raw')
        return w_res

    def _get_result(self, space, resultdata):
        w_info = self.w_info
        assert isinstance(w_info, W_FunctionTypeObject)
        w_ret_type = w_info.w_ret_type
        assert isinstance(w_ret_type, W_TypeObject)
        typeindex = w_ret_type.typeindex
        for c in ffitype.unrolling_types:
            if c == typeindex:
                return read_and_wrap_from_address(space, resultdata, c,
                                                  out=True)
        assert 0

    def _put_arg(self, space, data, i, w_obj):
        w_info = self.w_info
        assert isinstance(w_info, W_FunctionTypeObject)
        w_argtype = w_info.arg_types_w[i]
        if isinstance(w_argtype, W_FunctionTypeObject):
            self._push_callback(space, data, w_argtype, w_obj)
        elif isinstance(w_argtype, W_MappedObject):
            self._push_mapped(space, data, w_argtype, w_obj)
        else:
            self._push_ordinary(space, data, w_argtype, w_obj)

    def _push_callback(self, space, data, w_func_type, w_proc):
        cif_descr = w_func_type.build_cif_descr(space)
        callback_data = _callback.Data(space, w_proc, w_func_type)
        closure = _callback.Closure(callback_data)
        closure.write(data)

    def _push_mapped(self, space, data, w_mapped, w_obj):
        try:
            w_lookup = space.send(w_mapped, 'to_native', [w_obj, space.w_nil])
            enum_t = w_mapped.typeindex
            for t in ffitype.unrolling_types:
                if t == enum_t:
                    unwrap_and_write_to_address(space, w_lookup, data, t,
                                                out=False)
        except RubyError, argument_error:
            raise space.error(space.w_TypeError,
                              "`to_native': %s (ArgumentError)" %
                              argument_error.w_value.msg)

    def _push_ordinary(self, space, data, w_argtype, w_obj):
        assert isinstance(w_argtype, W_TypeObject)
        typeindex = w_argtype.typeindex
        for c in ffitype.unrolling_types:
            if c == typeindex:
                unwrap_and_write_to_address(space, w_obj, data, c, out=False)

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
