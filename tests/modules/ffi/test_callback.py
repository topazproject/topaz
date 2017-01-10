from topaz.modules.ffi import _callback

from rpython.rtyper.lltypesystem import lltype, rffi, llmemory
from rpython.rlib.jit_libffi import CIF_DESCRIPTION, CIF_DESCRIPTION_P
from rpython.rlib.objectmodel import compute_unique_id

def test_Data_invoke(space):
    w_func_type = space.execute("""
    int32 = FFI::Type::INT32
    func_type = FFI::FunctionType.new(int32,
                [int32, int32])
    """)
    w_proc = space.execute("proc { |x, y| x + y }")
    p_arg1 = lltype.malloc(rffi.CCHARP.TO, 1, flavor='raw')
    p_arg2 = lltype.malloc(rffi.CCHARP.TO, 1, flavor='raw')
    p_args = lltype.malloc(rffi.CCHARPP.TO, 2, flavor='raw')
    p_res = lltype.malloc(rffi.INTP.TO, 1, flavor='raw')
    try:
        p_arg1[0] = rffi.cast(rffi.CHAR, 1)
        p_arg2[0] = rffi.cast(rffi.CHAR, 2)
        p_args[0] = p_arg1
        p_args[1] = p_arg2
        callback_data = _callback.Data(space, w_proc, w_func_type)
        callback_data.invoke(p_args, p_res)
        assert p_res[0] == 3
    finally:
        lltype.free(p_arg1, flavor='raw')
        lltype.free(p_arg2, flavor='raw')
        lltype.free(p_args, flavor='raw')
        lltype.free(p_res, flavor='raw')

def test_invoke(space):
    size = llmemory.raw_malloc_usage(llmemory.sizeof(CIF_DESCRIPTION, 2))
    cif_descr = lltype.malloc(CIF_DESCRIPTION_P.TO, size, flavor='raw')
    p_arg1 = lltype.malloc(rffi.CCHARP.TO, 1, flavor='raw')
    p_arg2 = lltype.malloc(rffi.CCHARP.TO, 1, flavor='raw')
    p_args = lltype.malloc(rffi.CCHARPP.TO, 2, flavor='raw')
    p_res = lltype.malloc(rffi.INTP.TO, 1, flavor='raw')
    w_proc_mul = space.execute("proc { |x, y| x * y }")
    w_proc_diff = space.execute("proc { |x, y| (x - y).abs }")
    w_callback_info = space.execute("""
    int32 = FFI::Type::INT32
    func_type = FFI::FunctionType.new(int32,
                [int32, int32])
    """)
    data_mul_w = _callback.Data(space, w_proc_mul, w_callback_info)
    data_diff_w = _callback.Data(space, w_proc_diff, w_callback_info)
    id_mul = compute_unique_id(data_mul_w)
    id_diff = compute_unique_id(data_diff_w)
    _callback.registration[id_mul] = _callback.Closure(data_mul_w)
    _callback.registration[id_diff] = _callback.Closure(data_diff_w)
    try:
        p_arg1[0] = rffi.cast(rffi.CHAR, 6)
        p_arg2[0] = rffi.cast(rffi.CHAR, 7)
        p_args[0] = p_arg1
        p_args[1] = p_arg2
        _callback.invoke(cif_descr,
                         rffi.cast(rffi.VOIDP, p_res),
                         rffi.cast(rffi.VOIDPP, p_args),
                         rffi.cast(rffi.VOIDP, id_mul))
        assert p_res[0] == 42
        _callback.invoke(cif_descr,
                         rffi.cast(rffi.VOIDP, p_res),
                         rffi.cast(rffi.VOIDPP, p_args),
                         rffi.cast(rffi.VOIDP, id_diff))
        assert p_res[0] == 1
    finally:
        lltype.free(cif_descr, flavor='raw')
        lltype.free(p_arg1, flavor='raw')
        lltype.free(p_arg2, flavor='raw')
        lltype.free(p_args, flavor='raw')
        lltype.free(p_res, flavor='raw')
