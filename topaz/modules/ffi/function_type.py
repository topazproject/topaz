import sys
from topaz.modules.ffi.type import W_TypeObject, W_MappedObject
from topaz.modules.ffi import type as ffitype
from topaz.modules.ffi import _callback
from topaz.module import ClassDef

from rpython.rtyper.lltypesystem import rffi, llmemory, lltype
from rpython.rlib.jit_libffi import (CIF_DESCRIPTION, CIF_DESCRIPTION_P,
                                     FFI_TYPE_P, FFI_TYPE_PP, SIZE_OF_FFI_ARG)
from rpython.rlib.jit_libffi import jit_ffi_prep_cif, jit_ffi_call
from rpython.rlib import jit
from rpython.rlib.objectmodel import we_are_translated
from rpython.rlib import clibffi

BIG_ENDIAN = sys.byteorder == 'big'

def raise_TypeError_if_not_TypeObject(space, w_candidate):
    if not isinstance(w_candidate, W_TypeObject):
        raise space.error(space.w_TypeError,
                          "Invalid parameter type (%s)" %
                          space.str_w(space.send(w_candidate, 'inspect')))

class W_FunctionTypeObject(W_TypeObject):
    classdef = ClassDef('FFI::FunctionType', W_TypeObject.classdef)
    _immutable_fields_ = ['arg_types_w', 'w_ret_type', 'cif_descr']

    def __init__(self, space):
        W_TypeObject.__init__(self, space, ffitype.FUNCTION)
        self.cif_descr = lltype.nullptr(CIF_DESCRIPTION)

    def __del__(self):
        if self.cif_descr:
            lltype.free(self.cif_descr, flavor='raw')

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_FunctionTypeObject(space)

    @classdef.method('initialize', arg_types_w='array')
    def method_initialize(self, space, w_ret_type, arg_types_w, w_options=None):
        if w_options is None:
            w_options = space.newhash()
        self.w_options = w_options
        self.space = space

        raise_TypeError_if_not_TypeObject(space, w_ret_type)
        for w_arg_type in arg_types_w:
            raise_TypeError_if_not_TypeObject(space, w_arg_type)

        self.w_ret_type = w_ret_type
        self.arg_types_w = arg_types_w
        self.cif_descr = self.build_cif_descr(space)

    @jit.dont_look_inside
    def build_cif_descr(self, space):
        arg_types_w = self.arg_types_w
        w_ret_type = self.w_ret_type
        assert isinstance(w_ret_type, W_TypeObject)

        ffi_arg_types = []
        for w_arg_type in arg_types_w:
            assert isinstance(w_arg_type, W_TypeObject)
            ffi_arg_type = ffitype.ffi_types[w_arg_type.typeindex]
            ffi_arg_types.append(ffi_arg_type)
        ffi_ret_type = ffitype.ffi_types[w_ret_type.typeindex]

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
        status = jit_ffi_prep_cif(cif_descr)
        #
        if status != clibffi.FFI_OK:
            raise space.error(space.w_RuntimeError,
                    "libffi failed to build this function type")
        #
        return cif_descr

    @jit.unroll_safe
    def invoke(self, space, ptr, args_w, block=None):
        self = jit.promote(self)

        if block is not None:
            args_w.append(block)
        nargs = len(args_w)
        assert nargs == self.cif_descr.nargs
        #
        size = self.cif_descr.exchange_size
        buffer = lltype.malloc(rffi.CCHARP.TO, size, flavor='raw')
        try:
            for i in range(len(args_w)):
                data = rffi.ptradd(buffer, self.cif_descr.exchange_args[i])
                w_obj = args_w[i]
                self._put_arg(space, data, i, w_obj)

            #ec = cerrno.get_errno_container(space)
            #cerrno.restore_errno_from(ec)
            jit_ffi_call(self.cif_descr, rffi.cast(rffi.VOIDP, ptr), buffer)
            #e = cerrno.get_real_errno()
            #cerrno.save_errno_into(ec, e)

            resultdata = rffi.ptradd(buffer, self.cif_descr.exchange_result)
            w_res =  self._get_result(space, resultdata)
        finally:
            lltype.free(buffer, flavor='raw')
        return w_res

    def _get_result(self, space, resultdata):
        w_ret_type = self.w_ret_type
        assert isinstance(w_ret_type, W_TypeObject)
        return w_ret_type.read(space, resultdata)

    def _put_arg(self, space, data, i, w_obj):
        w_argtype = self.arg_types_w[i]
        assert isinstance(w_argtype, W_TypeObject)
        if w_argtype.typeindex == ffitype.VOID:
            raise space.error(space.w_ArgumentError,
                              "arguments cannot be of type void")
        w_argtype.write(space, data, w_obj)

    def align_arg(self, n):
        return (n + 7) & ~7

    def write(self, space, data, w_proc):
        callback_data = _callback.Data(space, w_proc, self)
        closure = _callback.Closure(callback_data)
        closure.write(data)
