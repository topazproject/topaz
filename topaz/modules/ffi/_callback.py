from rpython.rtyper.lltypesystem import rffi, lltype
from rpython.rlib.objectmodel import compute_unique_id
from rpython.rlib import clibffi, jit

from pypy.module._cffi_backend import misc

# This will definitely leak memory
registration = {}

class Data(object):
    def __init__(self, w_proc, w_callback_info):
        self.w_proc = w_proc
        self.w_callback_info = w_callback_info

    def invoke(self, args_ll, ll_res):
        self.w_callback_info.invoke(self.w_proc, ll_res, args_ll)

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
        #rffi.cast(rffi.CCHARPP, data)[0] = rffi.cast(rffi.CCHARP, self.heap)
        misc.write_raw_unsigned_data(data, rffi.cast(rffi.CCHARP, self.heap),
                                    rffi.sizeof(clibffi.FFI_CLOSUREP))

@jit.jit_callback("CFFI")
def invoke(ll_cif, ll_res, ll_args, ll_data):
    key = rffi.cast(lltype.Signed, ll_data)
    w_data = registration[key]
    w_data.invoke(ll_args, ll_res)
