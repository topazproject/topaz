from rpython.rtyper.lltypesystem import rffi

# This will definitely leak memory
registration = {}

def invoke(ll_cif, args_ll, ll_res, ll_data):
    key = rffi.cast(rffi.SIGNEDP, ll_data)[0]
    w_proc, w_func_type = registration[key]
    w_func_type.invoke(w_proc, args_ll, ll_res)
