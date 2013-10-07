import sys

from topaz.module import ClassDef
from topaz.modules.ffi import type as ffitype
from topaz.modules.ffi.pointer import W_PointerObject
from topaz.modules.ffi.dynamic_library import coerce_dl_symbol
from topaz.modules.ffi._ruby_wrap_llval import (_ruby_wrap_llpointer_content
                                                as _read_result,
                                                _ruby_unwrap_llpointer_content
                                                as _push_arg)
from topaz.modules.ffi.function_type import W_FunctionTypeObject
from topaz.modules.ffi import _callback

from rpython.rtyper.lltypesystem import rffi, lltype
from rpython.rlib import jit
from rpython.rlib.jit_libffi import CIF_DESCRIPTION
from rpython.rlib.jit_libffi import FFI_TYPE_PP
from rpython.rlib.jit_libffi import jit_ffi_call

# XXX maybe move to rlib/jit_libffi
from pypy.module._cffi_backend import misc

for i, name in enumerate(ffitype.type_names):
    globals()[name] = i

class W_FunctionObject(W_PointerObject):
    classdef = ClassDef('Function', W_PointerObject.classdef)
    _immutable_fields_ = ['cif_descr', 'atypes', 'ptr', 'arg_types_w', 'w_ret_type']

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_FunctionObject(space)

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
                          w_name=None, w_options=None):
        if w_options is None:
            w_options = space.newhash()

        self.w_info = space.send(space.getclassfor(W_FunctionTypeObject),
                                 'new', [w_ret_type, w_arg_types, w_options])
        self.setup(space, w_name)

    def setup(self, space, w_name):
        self.ptr = (coerce_dl_symbol(space, w_name) if w_name
                    else lltype.nullptr(rffi.VOIDP.TO))
        self.cif_descr = self.w_info.build_cif_descr(space)
        self.atypes = self.cif_descr.atypes

    def initialize_variadic(self, space, w_name, w_ret_type, arg_types_w):
        self.w_info = space.send(space.getclassfor(W_FunctionTypeObject),
                                 'new',
                                 [w_ret_type, space.newarray(arg_types_w)])
        self.setup(space, w_name)

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
        typeindex = self.w_info.w_ret_type.typeindex
        for c in ffitype.unrolling_types:
            if c == typeindex:
                return _read_result(space, resultdata, c)
        assert 0

    def _put_arg(self, space, data, i, w_obj):
        w_argtype = self.w_info.arg_types_w[i]
        if isinstance(w_argtype, W_FunctionTypeObject):
            self._push_callback(space, data, w_argtype, w_obj)
        else:
            self._push_ordinary(space, data, w_argtype, w_obj)

    def _push_callback(self, space, data, w_func_type, w_proc):
        cif_descr = w_func_type.build_cif_descr(space)
        callback_data = _callback.Data(space, w_proc, w_func_type)
        self.closure = _callback.Closure(cif_descr, callback_data)
        self.closure.write(data)

    def _push_ordinary(self, space, data, argtype, w_obj):
        typeindex = argtype.typeindex
        for c in ffitype.unrolling_types:
            if c == typeindex:
                _push_arg(space, w_obj, data, c)

    @classdef.method('attach', name='str')
    def method_attach(self, space, w_lib, name):
        w_attachments = space.send(w_lib, 'attachments')
        space.send(w_attachments, '[]=', [space.newsymbol(name), self])
