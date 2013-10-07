import sys

from topaz.objects.objectobject import W_Object
from topaz.module import ClassDef
from topaz.modules.ffi import type as ffitype
from topaz.modules.ffi.pointer import W_PointerObject
from topaz.modules.ffi.dynamic_library import (W_DL_SymbolObject,
                                               coerce_dl_symbol)
from topaz.modules.ffi._ruby_wrap_llval import (_ruby_wrap_number,
                                                _ruby_wrap_POINTER,
                                                _ruby_wrap_STRING,
                                                _ruby_wrap_llpointer_content
                                                as _read_result,
                                                _ruby_unwrap_llpointer_content
                                                as _push_arg)
from topaz.modules.ffi.function_type import W_FunctionTypeObject
from topaz.modules.ffi import _callback
from topaz.error import RubyError
from topaz.coerce import Coerce
from topaz.objects.functionobject import W_BuiltinFunction

from rpython.rtyper.lltypesystem import rffi, lltype, llmemory
from rpython.rtyper.lltypesystem.lltype import scoped_alloc
from rpython.rlib import clibffi, jit
from rpython.rlib.jit_libffi import CIF_DESCRIPTION, CIF_DESCRIPTION_P
from rpython.rlib.jit_libffi import FFI_TYPE_P, FFI_TYPE_PP
from rpython.rlib.jit_libffi import SIZE_OF_FFI_ARG
from rpython.rlib.jit_libffi import jit_ffi_call
from rpython.rlib.jit_libffi import jit_ffi_prep_cif
from rpython.rlib.objectmodel import specialize
from rpython.rlib.objectmodel import we_are_translated, compute_unique_id

# XXX maybe move to rlib/jit_libffi
from pypy.module._cffi_backend import misc

BIG_ENDIAN = sys.byteorder == 'big'

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
        ffi_arg_types = [ffitype.ffi_types[t.typeindex]
                         for t in self.w_info.arg_types_w]
        ffi_ret_type = ffitype.ffi_types[self.w_info.w_ret_type.typeindex]
        self.cif_descr = self.build_cif_descr(space, ffi_arg_types, ffi_ret_type)
        self.atypes = self.cif_descr.atypes

    def initialize_variadic(self, space, w_name, w_ret_type, arg_types_w):
        self.w_info = space.send(space.getclassfor(W_FunctionTypeObject),
                                 'new',
                                 [w_ret_type, space.newarray(arg_types_w)])
        self.setup(space, w_name)

    def align_arg(self, n):
        return (n + 7) & ~7

    @jit.dont_look_inside
    def build_cif_descr(self, space, ffi_arg_types, ffi_ret_type):
        nargs = len(ffi_arg_types)
        # XXX combine both mallocs with alignment
        size = llmemory.raw_malloc_usage(llmemory.sizeof(CIF_DESCRIPTION, nargs))
        if we_are_translated():
            cif_descr = lltype.malloc(rffi.CCHARP.TO, size, flavor='raw')
            cif_descr = rffi.cast(CIF_DESCRIPTION_P, cif_descr)
        else:
            # gross overestimation of the length below, but too bad
            cif_descr = lltype.malloc(CIF_DESCRIPTION_P.TO, size, flavor='raw')
        assert cif_descr
        #
        size = rffi.sizeof(FFI_TYPE_P) * nargs
        atypes = lltype.malloc(rffi.CCHARP.TO, size, flavor='raw')
        atypes = rffi.cast(FFI_TYPE_PP, atypes)
        assert atypes
        #
        cif_descr.abi = clibffi.FFI_DEFAULT_ABI
        cif_descr.nargs = nargs
        cif_descr.rtype = ffi_ret_type
        cif_descr.atypes = atypes
        #
        # first, enough room for an array of 'nargs' pointers
        exchange_offset = rffi.sizeof(rffi.CCHARP) * nargs
        exchange_offset = self.align_arg(exchange_offset)
        cif_descr.exchange_result = exchange_offset
        cif_descr.exchange_result_libffi = exchange_offset
        #
        if BIG_ENDIAN:
            assert 0, 'missing support'
            # see _cffi_backend in pypy
        # then enough room for the result, rounded up to sizeof(ffi_arg)
        exchange_offset += max(rffi.getintfield(ffi_ret_type, 'c_size'),
                               SIZE_OF_FFI_ARG)

        # loop over args
        for i, ffi_arg in enumerate(ffi_arg_types):
            # XXX do we need the "must free" logic?
            exchange_offset = self.align_arg(exchange_offset)
            cif_descr.exchange_args[i] = exchange_offset
            atypes[i] = ffi_arg
            exchange_offset += rffi.getintfield(ffi_arg, 'c_size')

        # store the exchange data size
        cif_descr.exchange_size = exchange_offset
        #
        res = jit_ffi_prep_cif(cif_descr)
        #
        if res != clibffi.FFI_OK:
            raise space.error(space.w_RuntimeError,
                    "libffi failed to build this function type")
        #
        return cif_descr

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
        ffi_arg_types = [ffitype.ffi_types[w_arg_type.typeindex]
                         for w_arg_type in w_func_type.arg_types_w]
        ffi_ret_type = ffitype.ffi_types[w_func_type.w_ret_type.typeindex]
        cif_descr = self.build_cif_descr(space, ffi_arg_types, ffi_ret_type)
        callback_data = _callback.Data(w_proc, w_func_type)
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
