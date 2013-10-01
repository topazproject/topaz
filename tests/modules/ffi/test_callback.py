from topaz.modules.ffi import _callback

from rpython.rtyper.lltypesystem import lltype, rffi, llmemory
from rpython.rlib.jit_libffi import CIF_DESCRIPTION, CIF_DESCRIPTION_P

def test_invoke(space):
    size = llmemory.raw_malloc_usage(llmemory.sizeof(CIF_DESCRIPTION, 2))
    cif_descr = lltype.malloc(CIF_DESCRIPTION_P.TO, size, flavor='raw')
    p_arg1 = lltype.malloc(rffi.INTP.TO, 1, flavor='raw')
    p_arg2 = lltype.malloc(rffi.INTP.TO, 1, flavor='raw')
    p_res = lltype.malloc(rffi.INTP.TO, 1, flavor='raw')
    w_proc_mul = space.execute("proc { |x, y| x * y }")
    w_proc_diff = space.execute("proc { |x, y| (x - y).abs }")
    w_type_descr = space.execute("""
    int32 = FFI::Type::INT32
    func_type = FFI::FunctionType.new(int32,
                [int32, int32])
    """)
    _callback.registration[123] = (w_proc_mul, w_type_descr)
    _callback.registration[468] = (w_proc_diff, w_type_descr)
    p_data1 = lltype.malloc(rffi.SIGNEDP.TO, 1, flavor='raw')
    p_data2 = lltype.malloc(rffi.SIGNEDP.TO, 1, flavor='raw')
    try:
        p_arg1[0] = rffi.cast(rffi.INT, 6)
        p_arg2[0] = rffi.cast(rffi.INT, 7)
        p_data1[0] = rffi.cast(rffi.SIGNED, 123)
        p_data2[0] = rffi.cast(rffi.SIGNED, 468)
        _callback.invoke(cif_descr, [p_arg1, p_arg2], p_res,
                         rffi.cast(rffi.VOIDP, p_data1))
        assert p_res[0] == 42
        _callback.invoke(cif_descr, [p_arg1, p_arg2], p_res,
                         rffi.cast(rffi.VOIDP, p_data2))
        assert p_res[0] == 1
    finally:
        lltype.free(cif_descr, flavor='raw')
        lltype.free(p_arg1, flavor='raw')
        lltype.free(p_arg2, flavor='raw')
        lltype.free(p_data1, flavor='raw')
        lltype.free(p_data2, flavor='raw')
        lltype.free(p_res, flavor='raw')
