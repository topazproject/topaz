import sys

from topaz.objects.objectobject import W_Object
from topaz.module import ClassDef
from topaz.modules.ffi import type as ffitype
from topaz.modules.ffi.type import (ffi_types, W_TypeObject, type_object)
from topaz.modules.ffi.dynamic_library import (W_DL_SymbolObject,
                                               coerce_dl_symbol)
from topaz.modules.ffi.pointer import W_PointerObject, coerce_pointer
from topaz.error import RubyError
from topaz.coerce import Coerce
from topaz.objects.functionobject import W_BuiltinFunction

from rpython.rtyper.lltypesystem import rffi, lltype, llmemory
from rpython.rtyper.lltypesystem.lltype import scoped_alloc
from rpython.rlib import clibffi
from rpython.rlib.jit_libffi import CIF_DESCRIPTION, CIF_DESCRIPTION_P
from rpython.rlib.jit_libffi import FFI_TYPE_P, FFI_TYPE_PP
from rpython.rlib.jit_libffi import SIZE_OF_FFI_ARG
from rpython.rlib.jit_libffi import jit_ffi_call
from rpython.rlib.jit_libffi import jit_ffi_prep_cif
from rpython.rlib.unroll import unrolling_iterable
from rpython.rlib.objectmodel import specialize
from rpython.rlib.rarithmetic import intmask, longlongmask
from rpython.rlib.rbigint import rbigint
from rpython.rlib.objectmodel import we_are_translated

# XXX maybe move to rlib/jit_libffi
from pypy.module._cffi_backend import misc

BIG_ENDIAN = sys.byteorder == 'big'

for i, name in enumerate(ffitype.type_names):
    globals()[name] = i

unrolling_types = unrolling_iterable(range(len(ffitype.type_names)))


class W_FunctionObject(W_PointerObject):
    classdef = ClassDef('Function', W_PointerObject.classdef)

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

        self.w_ret_type = type_object(space, w_ret_type)
        self.arg_types_w = [type_object(space, w_type)
                            for w_type in space.listview(w_arg_types)]
        self.setup(space, w_name)

    def setup(self, space, w_name):
        self.ptr = (coerce_dl_symbol(space, w_name) if w_name
                    else lltype.nullptr(rffi.VOIDP.TO))
        ffi_arg_types = [ffi_types[t.typeindex] for t in self.arg_types_w]
        ffi_ret_type = ffi_types[self.w_ret_type.typeindex]
        self.build_cif_descr(space, ffi_arg_types, ffi_ret_type)

    def initialize_variadic(self, space, w_name, w_ret_type, arg_types_w):
        self.w_ret_type = w_ret_type
        self.arg_types_w = arg_types_w
        self.setup(space, w_name)

    def align_arg(self, n):
        return (n + 7) & ~7

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


    @classdef.method('call')
    def method_call(self, space, args_w):
        cif_descr = self.cif_descr
        size = cif_descr.exchange_size
        mustfree_max_plus_1 = 0
        buffer = lltype.malloc(rffi.CCHARP.TO, size, flavor='raw')
        for i in range(len(args_w)):
            data = rffi.ptradd(buffer, cif_descr.exchange_args[i])
            w_obj = args_w[i]
            argtype = self.arg_types_w[i]
            typeindex = argtype.typeindex
            for c in unrolling_types:
                if c == typeindex:
                    self._push_arg(space, w_obj, data, c)

        #ec = cerrno.get_errno_container(space)
        #cerrno.restore_errno_from(ec)
        jit_ffi_call(cif_descr, rffi.cast(rffi.VOIDP, self.ptr),
                                buffer)
        #e = cerrno.get_real_errno()
        #cerrno.save_errno_into(ec, e)

        resultdata = rffi.ptradd(buffer, cif_descr.exchange_result)

        typeindex = self.w_ret_type.typeindex
        for c in unrolling_types:
            if c == typeindex:
                return self._read_result(space, resultdata, c)


    @specialize.arg(3)
    def _read_result(self, space, data, typeindex):
        if typeindex == VOID:
            return space.w_nil
        typesize = ffitype.lltype_sizes[typeindex]
        for t in unrolling_types:
            if t == typeindex:
                # XXX refactor
                if t == FLOAT64 or t == FLOAT32:
                    result = misc.read_raw_float_data(data, typesize)
                    return self._ruby_wrap_number(space, result, t)
                elif t == LONG or t == INT64 or t == INT32 or t == INT16 or t == INT8:
                    result = misc.read_raw_signed_data(data, typesize)
                    return self._ruby_wrap_number(space, result, t)
                elif t == BOOL:
                    result = bool(misc.read_raw_signed_data(data, typesize))
                    return self._ruby_wrap_number(space, result, t)
                elif t == ULONG or t == UINT64 or t == UINT32 or t == UINT16 or t == UINT8:
                    result = misc.read_raw_unsigned_data(data, typesize)
                    return self._ruby_wrap_number(space, result, t)
                elif t == STRING:
                    result = misc.read_raw_unsigned_data(data, typesize)
                    result = rffi.cast(rffi.CCHARP, result)
                    return self._ruby_wrap_STRING(space, result)
                elif t == POINTER:
                    result = misc.read_raw_unsigned_data(data, typesize)
                    result = rffi.cast(rffi.VOIDP, result)
                    return self._ruby_wrap_POINTER(space, result)
                else:
                    raise Exception("Bug in FFI: unknown Type %s" % ffitype.type_names[typeindex])

    def _convert_to_NULL_if_nil(self, space, w_arg):
        if w_arg is space.w_nil:
            w_FFI = space.find_const(space.w_kernel, 'FFI')
            w_Pointer = space.find_const(w_FFI, 'Pointer')
            return space.find_const(w_Pointer, 'NULL')
        else:
            return w_arg

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

    @specialize.arg(3)
    def _ruby_wrap_number(self, space, res, restype):
        if restype == INT8:
            if res >= 128:
                res -= 256
            return space.newint(res)
        elif (restype == UINT8 or
              restype == UINT16 or
              restype == UINT16 or
              restype == INT16 or
              restype == UINT32 or
              restype == INT32):
            return space.newint(intmask(res))
        elif restype == INT64 or restype == UINT64:
            bigint_res = rbigint.fromrarith_int(longlongmask(res))
            return space.newbigint_fromrbigint(bigint_res)
        elif restype == LONG or restype == ULONG:
            if rffi.sizeof(rffi.LONG) < 8:
                return space.newint(intmask(res))
            else:
                bigint_res = rbigint.fromrarith_int(longlongmask(res))
                return space.newbigint_fromrbigint(bigint_res)
        elif restype == FLOAT32 or restype == FLOAT64:
            return space.newfloat(float(res))
        elif restype == BOOL:
            return space.newbool(res)
        raise Exception("Bug in FFI: unknown Type %s" % restype)

    def _ruby_wrap_STRING(self, space, res):
        str_res = rffi.charp2str(res)
        return space.newstr_fromstr(str_res)

    def _ruby_wrap_POINTER(self, space, res):
        adr_res = llmemory.cast_ptr_to_adr(res)
        int_res = llmemory.cast_adr_to_int(adr_res)
        w_FFI = space.find_const(space.w_kernel, 'FFI')
        w_Pointer = space.find_const(w_FFI, 'Pointer')
        return space.send(w_Pointer, 'new',
                          [space.newint(int_res)])

    @classdef.method('attach', name='str')
    def method_attach(self, space, w_lib, name):
        w_attachments = space.send(w_lib, 'attachments')
        space.send(w_attachments, '[]=', [space.newsymbol(name), self])
