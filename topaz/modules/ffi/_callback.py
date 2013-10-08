from topaz.modules.ffi import type as ffitype
from topaz.modules.ffi.type import W_TypeObject
from topaz.modules.ffi._memory_access import (read_and_wrap_from_address,
                                              unwrap_and_write_to_address)

from rpython.rtyper.lltypesystem import rffi, lltype
from rpython.rlib.objectmodel import compute_unique_id
from rpython.rlib import clibffi, jit

from pypy.module._cffi_backend import misc

# This will definitely leak memory
registration = {}

class Data(object):
    def __init__(self, space, w_proc, w_callback_info):
        self.space = space
        self.w_proc = w_proc
        self.w_callback_info = w_callback_info

    def invoke(self, ll_args, ll_res):
        space = self.space
        args_w = []
        for i in range(len(self.w_callback_info.arg_types_w)):
            w_arg_type = self.w_callback_info.arg_types_w[i]
            ll_arg = rffi.cast(rffi.CCHARP, ll_args[i])
            w_arg = self._read_and_wrap_llpointer(space, ll_arg, w_arg_type)
            args_w.append(w_arg)
        w_res = space.send(self.w_proc, 'call', args_w)
        self._unwrap_and_write_rubyobj(space, w_res, ll_res)

    def _read_and_wrap_llpointer(self, space, ll_adr, w_arg_type):
        assert isinstance(w_arg_type, W_TypeObject)
        typeindex = w_arg_type.typeindex
        for t in ffitype.unrolling_types:
            if t == typeindex:
                return read_and_wrap_from_address(space, ll_adr, t)
        assert 0

    def _unwrap_and_write_rubyobj(self, space, w_obj, ll_adr):
        ll_adr = rffi.cast(rffi.CCHARP, ll_adr)
        w_ret_type = self.w_callback_info.w_ret_type
        assert isinstance(w_ret_type, W_TypeObject)
        typeindex = w_ret_type.typeindex
        for t in ffitype.unrolling_types:
            if t == typeindex:
                unwrap_and_write_to_address(space, w_obj, ll_adr, t)

class Closure(object):
    def __init__(self, callback_data):
        self.heap = clibffi.closureHeap.alloc()
        self.callback_data = callback_data
        w_callback_info = self.callback_data.w_callback_info
        space = self.callback_data.space
        self.cif_descr = w_callback_info.build_cif_descr(space)
        self.uid = compute_unique_id(self.callback_data)
        registration[self.uid] = self.callback_data
        res = clibffi.c_ffi_prep_closure(rffi.cast(clibffi.FFI_CLOSUREP, self.heap),
                                         self.cif_descr.cif,
                                         invoke,
                                         rffi.cast(rffi.VOIDP, self.uid))
        if rffi.cast(lltype.Signed, res) != clibffi.FFI_OK:
            space = self.callback_data.space
            raise space.error(space.w_RuntimeError,
                              "libffi failed to build this callback type")

    def __del__(self):
        if self.heap:
            clibffi.closureHeap.free(self.heap)
        if self.cif_descr:
            lltype.free(self.cif_descr, flavor='raw')

    def write(self, data):
        misc.write_raw_unsigned_data(data, rffi.cast(rffi.CCHARP, self.heap),
                                    rffi.sizeof(clibffi.FFI_CLOSUREP))

@jit.jit_callback("CFFI")
def invoke(ll_cif, ll_res, ll_args, ll_data):
    key = rffi.cast(lltype.Signed, ll_data)
    w_data = registration[key]
    w_data.invoke(ll_args, ll_res)
