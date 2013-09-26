import sys

from topaz.objects.objectobject import W_Object
from topaz.module import ClassDef
from topaz.modules.ffi import type as ffitype
from topaz.modules.ffi.dynamic_library import (W_DL_SymbolObject,
                                               coerce_dl_symbol)
from topaz.modules.ffi.pointer import W_PointerObject, coerce_pointer
from topaz.modules.ffi._ruby_wrap_llval import (_ruby_wrap_number,
                                                _ruby_wrap_POINTER,
                                                _ruby_wrap_STRING)
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
from rpython.rlib.unroll import unrolling_iterable
from rpython.rlib.objectmodel import specialize
from rpython.rlib.objectmodel import we_are_translated

# XXX maybe move to rlib/jit_libffi
from pypy.module._cffi_backend import misc

BIG_ENDIAN = sys.byteorder == 'big'

for i, name in enumerate(ffitype.type_names):
    globals()[name] = i

unrolling_types = unrolling_iterable(range(len(ffitype.type_names)))


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

    @classdef.method('initialize', arg_types_w='array')
    def method_initialize(self, space, w_ret_type, arg_types_w,
                          w_name=None, w_options=None):
        if w_options is None:
            w_options = space.newhash()

        self.w_ret_type = ffitype.type_object(space, w_ret_type)
        self.arg_types_w = [ffitype.type_object(space, w_type)
                            for w_type in arg_types_w]
        self.setup(space, w_name)

    def setup(self, space, w_name):
        self.ptr = (coerce_dl_symbol(space, w_name) if w_name
                    else lltype.nullptr(rffi.VOIDP.TO))
        ffi_arg_types = [ffitype.ffi_types[t.typeindex] for t in self.arg_types_w]
        ffi_ret_type = ffitype.ffi_types[self.w_ret_type.typeindex]
        self.build_cif_descr(space, ffi_arg_types, ffi_ret_type)

    def initialize_variadic(self, space, w_name, w_ret_type, arg_types_w):
        self.w_ret_type = w_ret_type
        self.arg_types_w = arg_types_w
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
        self.cif_descr = cif_descr
        self.atypes = atypes
        #
        res = jit_ffi_prep_cif(cif_descr)
        #
        if res != clibffi.FFI_OK:
            raise space.error(space.w_RuntimeError,
                    "libffi failed to build this function type")

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
        typeindex = self.w_ret_type.typeindex
        for c in unrolling_types:
            if c == typeindex:
                return self._read_result(space, resultdata, c)
        assert 0



    @specialize.arg(3)
    def _read_result(self, space, data, t):
        if t == VOID:
            return space.w_nil
        typesize = ffitype.lltype_sizes[t]
        # XXX refactor
        if t == FLOAT64 or t == FLOAT32:
            result = misc.read_raw_float_data(data, typesize)
            return _ruby_wrap_number(space, result, t)
        elif t == LONG or t == INT64 or t == INT32 or t == INT16 or t == INT8:
            result = misc.read_raw_signed_data(data, typesize)
            return _ruby_wrap_number(space, result, t)
        elif t == BOOL:
            result = bool(misc.read_raw_signed_data(data, typesize))
            return _ruby_wrap_number(space, result, t)
        elif t == ULONG or t == UINT64 or t == UINT32 or t == UINT16 or t == UINT8:
            result = misc.read_raw_unsigned_data(data, typesize)
            return _ruby_wrap_number(space, result, t)
        elif t == STRING:
            result = misc.read_raw_unsigned_data(data, typesize)
            result = rffi.cast(rffi.CCHARP, result)
            return _ruby_wrap_STRING(space, result)
        elif t == POINTER:
            result = misc.read_raw_unsigned_data(data, typesize)
            result = rffi.cast(rffi.VOIDP, result)
            return _ruby_wrap_POINTER(space, result)
        raise Exception("Bug in FFI: unknown Type %s" % ffitype.type_names[t])

    def _convert_to_NULL_if_nil(self, space, w_arg):
        if w_arg is space.w_nil:
            w_FFI = space.find_const(space.w_kernel, 'FFI')
            w_Pointer = space.find_const(w_FFI, 'Pointer')
            return space.find_const(w_Pointer, 'NULL')
        else:
            return w_arg

    def _put_arg(self, space, data, i, w_obj):
        argtype = self.arg_types_w[i]
        typeindex = argtype.typeindex
        for c in unrolling_types:
            if c == typeindex:
                return self._push_arg(space, w_obj, data, c)
        assert 0

    @specialize.arg(4)
    def _push_arg(self, space, w_arg, data, typeindex):
        typesize = ffitype.lltype_sizes[typeindex]
        for t in unrolling_types:
            # XXX refactor
            if typeindex == t:
                if t == FLOAT32 or t == FLOAT64:
                    arg = space.float_w(w_arg)
                    misc.write_raw_float_data(data, arg, typesize)
                elif t == LONG or t == INT64 or t == INT8 or t == INT16 or t == INT32:
                    arg = space.int_w(w_arg)
                    misc.write_raw_signed_data(data, arg, typesize)
                elif t == ULONG or t == UINT64 or t == UINT8 or t == UINT16 or t == UINT32:
                    arg = space.int_w(w_arg)
                    misc.write_raw_unsigned_data(data, arg, typesize)
                elif t == STRING:
                    arg = space.str_w(w_arg)
                    arg = rffi.str2charp(arg)
                    arg = rffi.cast(lltype.Unsigned, arg)
                    misc.write_raw_unsigned_data(data, arg, typesize)
                elif t == BOOL:
                    arg = space.is_true(w_arg)
                    misc.write_raw_unsigned_data(data, arg, typesize)
                elif t == POINTER:
                    w_arg = self._convert_to_NULL_if_nil(space, w_arg)
                    arg = coerce_pointer(space, w_arg)
                    arg = rffi.cast(lltype.Unsigned, arg)
                    misc.write_raw_unsigned_data(data, arg, typesize)
                else:
                    assert 0
        return

    @classdef.method('attach', name='str')
    def method_attach(self, space, w_lib, name):
        w_attachments = space.send(w_lib, 'attachments')
        space.send(w_attachments, '[]=', [space.newsymbol(name), self])
