from topaz.modules.ffi import type as ffitype

from rpython.rtyper.lltypesystem import rffi, lltype
from rpython.rlib.objectmodel import specialize
from rpython.rlib.rarithmetic import intmask, longlongmask
from rpython.rlib.rbigint import rbigint

for i, name in enumerate(ffitype.type_names):
    globals()[name] = i

@specialize.arg(2)
def _ruby_wrap_number(space, res, restype):
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

def _ruby_wrap_STRING(space, res):
    str_res = rffi.charp2str(res)
    return space.newstr_fromstr(str_res)

def _ruby_wrap_POINTER(space, res):
    int_res = rffi.cast(lltype.Signed, res)
    w_FFI = space.find_const(space.w_kernel, 'FFI')
    w_Pointer = space.find_const(w_FFI, 'Pointer')
    return space.send(w_Pointer, 'new',
                      [space.newint(int_res)])
