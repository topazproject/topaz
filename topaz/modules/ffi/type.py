from topaz.objects.objectobject import W_Object
from topaz.module import ClassDef
from topaz.error import RubyError

from rpython.rlib.jit_libffi import FFI_TYPE_P
from rpython.rlib import clibffi
from rpython.rlib.rbigint import rbigint
from rpython.rtyper.lltypesystem import rffi, lltype
from rpython.rlib.rarithmetic import intmask
from topaz.coerce import Coerce

# XXX maybe move to rlib/jit_libffi
from pypy.module._cffi_backend import misc

_native_types = [
    ('VOID',       clibffi.ffi_type_void,                     lltype.Void,     []),
    ('INT8',       clibffi.ffi_type_sint8,                    rffi.CHAR,       ['CHAR', 'SCHAR']),
    ('UINT8',      clibffi.ffi_type_uint8,                    rffi.UCHAR,      ['UCHAR']),
    ('INT16',      clibffi.ffi_type_sint16,                   rffi.SHORT,      ['SHORT', 'SSHORT']),
    ('UINT16',     clibffi.ffi_type_uint16,                   rffi.USHORT,     ['USHORT']),
    ('INT32',      clibffi.ffi_type_sint32,                   rffi.INT,        ['INT', 'SINT']),
    ('UINT32',     clibffi.ffi_type_uint32,                   rffi.UINT,       ['UINT']),
    ('INT64',      clibffi.ffi_type_sint64,                   rffi.LONGLONG,   ['LONG_LONG', 'SLONG_LONG']),
    ('UINT64',     clibffi.ffi_type_uint64,                   rffi.ULONGLONG,  ['ULONG_LONG']),
    ('LONG',       clibffi.cast_type_to_ffitype(rffi.LONG),   rffi.LONG,       ['SLONG']),
    ('ULONG',      clibffi.cast_type_to_ffitype(rffi.ULONG),  rffi.ULONG,      []),
    ('FLOAT32',    clibffi.ffi_type_float,                    rffi.FLOAT,      ['FLOAT']),
    ('FLOAT64',    clibffi.ffi_type_double,                   rffi.DOUBLE,     ['DOUBLE']),
    ('LONGDOUBLE', clibffi.ffi_type_longdouble,               rffi.LONGDOUBLE, []),
    ('POINTER',    clibffi.ffi_type_pointer,                  rffi.VOIDP,      []),
    ('CALLBACK',   clibffi.ffi_type_pointer,                  rffi.VOIDP,      []),
    ('FUNCTION',   clibffi.ffi_type_pointer,                  rffi.VOIDP,      []),
    ('BUFFER_IN',),
    ('BUFFER_OUT',),
    ('BUFFER_INOUT',),
    ('CHAR_ARRAY',),
    ('BOOL',       clibffi.cast_type_to_ffitype(lltype.Bool), lltype.Bool,     []),
    ('STRING',     clibffi.ffi_type_pointer,                  rffi.CCHARP,     []),
    ('VARARGS',    clibffi.ffi_type_void,                     rffi.CHAR,       []),
    ('NATIVE_VARARGS',),
    ('NATIVE_STRUCT',),
    ('NATIVE_ARRAY',),
    ('NATIVE_MAPPED', clibffi.ffi_type_void,                  rffi.CCHARP,     []),
]

ffi_types = []
type_names = []
lltypes = []
lltype_sizes = []
aliases = []

for i, typ in enumerate(_native_types):
    type_names.append(typ[0])
    globals()[typ[0]] = i
    if len(typ) == 1:
        ffi_types.append(lltype.nullptr(FFI_TYPE_P.TO))
        lltype_sizes.append(0)
        aliases.append([])
        continue
    ffi_types.append(typ[1])
    lltypes.append(typ[2])
    aliases.append(typ[3])
    if typ[0] == 'VOID':
        lltype_sizes.append(-1)
    else:
        lltype_sizes.append(rffi.sizeof(lltypes[-1]))

del _native_types

def lltype_for_name(name):
    """NOT_RPYTHON"""
    # XXX maybe use a dictionary
    return lltypes[type_names.index(name)]

def size_for_name(name):
    """NOT_RPYTHON"""
    # XXX maybe use a dictionary
    return lltype_sizes[type_names.index(name)]


class W_TypeObject(W_Object):
    classdef = ClassDef('FFI::Type', W_Object.classdef)

    typeindex = 0
    _immutable_fields_ = ['typeindex', 'rw_strategy']

    def __init__(self, space, typeindex=0, rw_strategy=None, klass=None):
        assert isinstance(typeindex, int)
        W_Object.__init__(self, space, klass)
        self.typeindex = typeindex
        self.rw_strategy = rw_strategy

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        for t in rw_strategies:
            w_new_type = W_BuiltinType(space, t, rw_strategies[t])
            space.set_const(w_cls, type_names[t], w_new_type)
            for alias in aliases[t]:
                space.set_const(w_cls, alias, w_new_type)
        space.set_const(w_cls, 'Mapped', space.getclassfor(W_MappedObject))

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_TypeObject(space, VOID)

    def __deepcopy__(self, memo):
        obj = super(W_TypeObject, self).__deepcopy__(memo)
        obj.typeindex = self.typeindex
        obj.rw_strategy = self.rw_strategy
        return obj

    def __repr__(self):
        return '<W_TypeObject %s(%s)>' % (type_names[self.typeindex], lltype_sizes[self.typeindex])

    def eq(self, w_other):
        if not isinstance(w_other, W_TypeObject):
            return False
        return self.typeindex == w_other.typeindex

    __eq__ = eq

    @classdef.method('==')
    def method_eq(self, space, w_other):
        return space.newbool(self.eq(w_other))

    @classdef.method('size')
    def method_size(self, space):
        r_uint_size = lltype_sizes[self.typeindex]
        size = intmask(r_uint_size)
        return space.newint(size)

    def read(self, space, data):
        return self.rw_strategy.read(space, data)

    def write(self, space, data, w_arg):
        return self.rw_strategy.write(space, data, w_arg)

class W_BuiltinType(W_TypeObject):
    classdef = ClassDef('Builtin', W_TypeObject.classdef)

    def __init__(self, space, typeindex, rw_strategy):
        W_TypeObject.__init__(self, space, typeindex, rw_strategy)

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        raise NotImplementedError

def type_object(space, w_obj):
    w_ffi_mod = space.find_const(space.w_kernel, 'FFI')
    w_type = space.send(w_ffi_mod, 'find_type', [w_obj])
    if not isinstance(w_type, W_TypeObject):
        raise space.error(space.w_TypeError,
                          "This seems to be a bug. find_type should always"
                           "return an FFI::Type object, but apparently it did"
                           "not in this case.")
    return w_type

class ReadWriteStrategy(object):
    def __init__(self, typeindex):
        self.typesize = lltype_sizes[typeindex]

    def read(self, space, data):
        raise NotImplementedError("abstract ReadWriteStrategy")

    def write(self, space, data, w_arg):
        raise NotImplementedError("abstract ReadWriteStrategy")

class StringRWStrategy(ReadWriteStrategy):
    def __init__(self):
        ReadWriteStrategy.__init__(self, STRING)

    def read(self, space, data):
        result = misc.read_raw_unsigned_data(data, self.typesize)
        result = rffi.cast(rffi.CCHARP, result)
        result = rffi.charp2str(result)
        return space.newstr_fromstr(result)

    def write(self, space, data, w_arg):
        arg = space.str_w(w_arg)
        arg = rffi.str2charp(arg)
        arg = rffi.cast(lltype.Unsigned, arg)
        misc.write_raw_unsigned_data(data, arg, self.typesize)

class PointerRWStrategy(ReadWriteStrategy):
    def __init__(self):
        ReadWriteStrategy.__init__(self, POINTER)

    def read(self, space, data):
        result = misc.read_raw_unsigned_data(data, self.typesize)
        result = rffi.cast(lltype.Signed, result)
        w_FFI = space.find_const(space.w_kernel, 'FFI')
        w_Pointer = space.find_const(w_FFI, 'Pointer')
        return space.send(w_Pointer, 'new',
                          [space.newint(result)])

    def write(self, space, data, w_arg):
        w_arg = self._convert_to_NULL_if_nil(space, w_arg)
        arg = Coerce.ffi_pointer(space, w_arg)
        arg = rffi.cast(lltype.Unsigned, arg)
        misc.write_raw_unsigned_data(data, arg, self.typesize)

    @staticmethod
    def _convert_to_NULL_if_nil(space, w_arg):
        if w_arg is space.w_nil:
            w_FFI = space.find_const(space.w_kernel, 'FFI')
            w_Pointer = space.find_const(w_FFI, 'Pointer')
            return space.find_const(w_Pointer, 'NULL')
        else:
            return w_arg

class BoolRWStrategy(ReadWriteStrategy):
    def __init__(self):
        ReadWriteStrategy.__init__(self, BOOL)

    def read(self, space, data):
        result = bool(misc.read_raw_signed_data(data, self.typesize))
        return space.newbool(result)

    def write(self, space, data, w_arg):
        arg = space.is_true(w_arg)
        misc.write_raw_unsigned_data(data, arg, self.typesize)

class FloatRWStrategy(ReadWriteStrategy):
    def read(self, space, data):
        result = misc.read_raw_float_data(data, self.typesize)
        return space.newfloat(float(result))

    def write(self, space, data, w_arg):
        arg = space.float_w(w_arg)
        misc.write_raw_float_data(data, arg, self.typesize)

class SignedRWStrategy(ReadWriteStrategy):
    def read(self, space, data):
        result = misc.read_raw_signed_data(data, self.typesize)
        return space.newint(intmask(result))

    def write(self, space, data, w_arg):
        arg = space.int_w(w_arg)
        misc.write_raw_signed_data(data, arg, self.typesize)

class UnsignedRWStrategy(ReadWriteStrategy):
    def read(self, space, data):
        result = misc.read_raw_unsigned_data(data, self.typesize)
        return space.newint(intmask(result))

    def write(self, space, data, w_arg):
        arg = space.int_w(w_arg)
        misc.write_raw_unsigned_data(data, arg, self.typesize)

class VoidRWStrategy(ReadWriteStrategy):
    def __init__(self):
        ReadWriteStrategy.__init__(self, VOID)

    def read(self, space, data):
        return space.w_nil;

    def write(self, space, data, w_arg):
        pass

rw_strategies = {}
rw_strategies[VOID] = VoidRWStrategy()
for ts, tu in [[INT8, UINT8],
              [INT16, UINT16],
              [INT32, UINT32],
              [INT64, UINT64],
              [LONG, ULONG]]:
    rw_strategies[ts] = SignedRWStrategy(ts)
    rw_strategies[tu] = UnsignedRWStrategy(tu)
# LongdoubleRWStrategy is not implemented yet, give LONGDOUBLE a
# FloatRWStrategy for now so the ruby part of ffi doesn't crash when it gets
# loaded
for t in [FLOAT32, FLOAT64, LONGDOUBLE]:
    rw_strategies[t] = FloatRWStrategy(t)
rw_strategies[POINTER] = PointerRWStrategy()
rw_strategies[BOOL] = BoolRWStrategy()
rw_strategies[STRING] = StringRWStrategy()
# These three are not implemented yet, they just get a pointer strategy for now
# to make the ruby part happy
for t in [BUFFER_IN, BUFFER_OUT, BUFFER_INOUT]:
    rw_strategies[t] = PointerRWStrategy()
rw_strategies[VARARGS] = VoidRWStrategy()

class W_MappedObject(W_TypeObject):
    classdef = ClassDef('MappedObject', W_TypeObject.classdef)

    def __init__(self, space, klass=None):
        W_TypeObject.__init__(self, space, NATIVE_MAPPED)
        self.rw_strategy = None

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_MappedObject(space)

    @classdef.method('initialize')
    def method_initialize(self, space, w_data_converter):
        for required in ['native_type', 'to_native', 'from_native']:
            if not space.respond_to(w_data_converter, required):
                raise space.error(space.w_NoMethodError,
                                  "%s method not implemented" % required)
        self.w_data_converter = w_data_converter
        w_type = space.send(w_data_converter, 'native_type')
        if isinstance(w_type, W_TypeObject):
            self.typeindex = w_type.typeindex
            self.rw_strategy = w_type.rw_strategy
        else:
            raise space.error(space.w_TypeError,
                              "native_type did not return instance of "
                              "FFI::Type")

    @classdef.method('to_native')
    def method_to_native(self, space, args_w):
        return space.send(self.w_data_converter, 'to_native', args_w)

    @classdef.method('from_native')
    def method_from_native(self, space, args_w):
        return space.send(self.w_data_converter, 'from_native', args_w)

    def read(self, space, data):
        w_native = W_TypeObject.read(self, space, data)
        return self.method_from_native(space, [w_native, space.w_nil])

    def write(self, space, data, w_obj):
        w_lookup = self.method_to_native(space, [w_obj, space.w_nil])
        W_TypeObject.write(self, space, data, w_lookup)
