registration = {}

def invoke(ll_cif, args_ll, ll_res, ll_data):
    key = ll_data[0]
    w_proc, w_func_type = registration[key]
    w_func_type.invoke(w_proc, args_ll, ll_res)
