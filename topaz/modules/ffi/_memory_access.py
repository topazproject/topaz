from topaz.modules.ffi import type as ffitype
from topaz.modules.ffi.pointer import coerce_pointer

from rpython.rtyper.lltypesystem import rffi, lltype
from rpython.rlib.objectmodel import specialize
from rpython.rlib.rarithmetic import intmask, longlongmask
from rpython.rlib.rbigint import rbigint
from rpython.rlib.unroll import unrolling_iterable

# XXX maybe move to rlib/jit_libffi
from pypy.module._cffi_backend import misc

for i, name in enumerate(ffitype.type_names):
    globals()[name] = i

unrolling_types = unrolling_iterable(range(len(ffitype.type_names)))

@specialize.arg(2)
def read_and_wrap_from_address(space, data, t):
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

@specialize.arg(3)
def unwrap_and_write_to_address(space, w_arg, data, typeindex):
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
                w_arg = _convert_to_NULL_if_nil(space, w_arg)
                arg = coerce_pointer(space, w_arg)
                arg = rffi.cast(lltype.Unsigned, arg)
                misc.write_raw_unsigned_data(data, arg, typesize)
            else:
                assert 0
    return

def _convert_to_NULL_if_nil(space, w_arg):
    if w_arg is space.w_nil:
        w_FFI = space.find_const(space.w_kernel, 'FFI')
        w_Pointer = space.find_const(w_FFI, 'Pointer')
        return space.find_const(w_Pointer, 'NULL')
    else:
        return w_arg
