from topaz.modules.ffi import type as ffitype
from topaz.modules.ffi.type import W_TypeObject
from topaz.modules.ffi._ruby_wrap_llval import (_ruby_wrap_llpointer_content,
                                                _ruby_unwrap_llpointer_content)

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

    def _read_and_wrap_llpointer(self, space, llp, w_arg_type):
        assert isinstance(w_arg_type, W_TypeObject)
        typeindex = w_arg_type.typeindex
        for t in ffitype.unrolling_types:
            if t == typeindex:
                return _ruby_wrap_llpointer_content(space, llp, t)
        assert 0

    def _unwrap_and_write_rubyobj(self, space, w_obj, ll_val):
        ll_val = rffi.cast(rffi.CCHARP, ll_val)
        w_ret_type = self.w_callback_info.w_ret_type
        assert isinstance(w_ret_type, W_TypeObject)
        typeindex = w_ret_type.typeindex
        for t in ffitype.unrolling_types:
            if t == typeindex:
                _ruby_unwrap_llpointer_content(space, w_obj, ll_val, t)

class Closure(object):
    def __init__(self, cif_descr, callback_data):
        self.heap = clibffi.closureHeap.alloc()
        self.cif_descr = cif_descr
        self.callback_data = callback_data
        self.uid = compute_unique_id(self.callback_data)
        registration[self.uid] = self.callback_data
        res = clibffi.c_ffi_prep_closure(rffi.cast(clibffi.FFI_CLOSUREP, self.heap),
                                         self.cif_descr.cif,
                                         invoke,
                                         rffi.cast(rffi.VOIDP, self.uid))
        if rffi.cast(lltype.Signed, res) != clibffi.FFI_OK:
            raise Exception("preparing the closure failed!")

    def write(self, data):
        misc.write_raw_unsigned_data(data, rffi.cast(rffi.CCHARP, self.heap),
                                    rffi.sizeof(clibffi.FFI_CLOSUREP))

@jit.jit_callback("CFFI")
def invoke(ll_cif, ll_res, ll_args, ll_data):
    key = rffi.cast(lltype.Signed, ll_data)
    w_data = registration[key]
    w_data.invoke(ll_args, ll_res)
