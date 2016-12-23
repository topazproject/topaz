from rpython.rlib.objectmodel import specialize
from rpython.rtyper.lltypesystem import lltype, rffi
from rpython.rlib.unroll import unrolling_iterable


_prim_signed_types = unrolling_iterable([
    (rffi.SIGNEDCHAR, rffi.SIGNEDCHARP),
    (rffi.SHORT, rffi.SHORTP),
    (rffi.INT, rffi.INTP),
    (rffi.LONG, rffi.LONGP),
    (rffi.LONGLONG, rffi.LONGLONGP)])

_prim_unsigned_types = unrolling_iterable([
    (rffi.UCHAR, rffi.UCHARP),
    (rffi.USHORT, rffi.USHORTP),
    (rffi.UINT, rffi.UINTP),
    (rffi.ULONG, rffi.ULONGP),
    (rffi.ULONGLONG, rffi.ULONGLONGP)])

_prim_float_types = unrolling_iterable([
    (rffi.FLOAT, rffi.FLOATP),
    (rffi.DOUBLE, rffi.DOUBLEP)])


def read_raw_signed_data(target, size):
    for TP, TPP in _prim_signed_types:
        if size == rffi.sizeof(TP):
            return rffi.cast(lltype.SignedLongLong, rffi.cast(TPP, target)[0])
    raise NotImplementedError("bad integer size")

def read_raw_long_data(target, size):
    for TP, TPP in _prim_signed_types:
        if size == rffi.sizeof(TP):
            assert rffi.sizeof(TP) <= rffi.sizeof(lltype.Signed)
            return rffi.cast(lltype.Signed, rffi.cast(TPP, target)[0])
    raise NotImplementedError("bad integer size")

def read_raw_unsigned_data(target, size):
    for TP, TPP in _prim_unsigned_types:
        if size == rffi.sizeof(TP):
            return rffi.cast(lltype.UnsignedLongLong, rffi.cast(TPP, target)[0])
    raise NotImplementedError("bad integer size")

def read_raw_ulong_data(target, size):
    for TP, TPP in _prim_unsigned_types:
        if size == rffi.sizeof(TP):
            assert rffi.sizeof(TP) <= rffi.sizeof(lltype.Unsigned)
            return rffi.cast(lltype.Unsigned, rffi.cast(TPP, target)[0])
    raise NotImplementedError("bad integer size")

@specialize.arg(0)
def _read_raw_float_data_tp(TPP, target):
    # in its own function: FLOAT may make the whole function jit-opaque
    return rffi.cast(lltype.Float, rffi.cast(TPP, target)[0])

def read_raw_float_data(target, size):
    for TP, TPP in _prim_float_types:
        if size == rffi.sizeof(TP):
            return _read_raw_float_data_tp(TPP, target)
    raise NotImplementedError("bad float size")

def read_raw_longdouble_data(target):
    return rffi.cast(rffi.LONGDOUBLEP, target)[0]

@specialize.argtype(1)
def write_raw_unsigned_data(target, source, size):
    for TP, TPP in _prim_unsigned_types:
        if size == rffi.sizeof(TP):
            rffi.cast(TPP, target)[0] = rffi.cast(TP, source)
            return
    raise NotImplementedError("bad integer size")

@specialize.argtype(1)
def write_raw_signed_data(target, source, size):
    for TP, TPP in _prim_signed_types:
        if size == rffi.sizeof(TP):
            rffi.cast(TPP, target)[0] = rffi.cast(TP, source)
            return
    raise NotImplementedError("bad integer size")


@specialize.arg(0, 1)
def _write_raw_float_data_tp(TP, TPP, target, source):
    # in its own function: FLOAT may make the whole function jit-opaque
    rffi.cast(TPP, target)[0] = rffi.cast(TP, source)

def write_raw_float_data(target, source, size):
    for TP, TPP in _prim_float_types:
        if size == rffi.sizeof(TP):
            _write_raw_float_data_tp(TP, TPP, target, source)
            return
    raise NotImplementedError("bad float size")

def write_raw_longdouble_data(target, source):
    rffi.cast(rffi.LONGDOUBLEP, target)[0] = source
