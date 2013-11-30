from topaz.objects.objectobject import W_Object
from topaz.module import ClassDef

from rpython.rlib.jit_libffi import FFI_TYPE_P
from rpython.rlib import clibffi
from rpython.rlib.rbigint import rbigint
from rpython.rtyper.lltypesystem import rffi, lltype
from rpython.rlib.rarithmetic import intmask
from rpython.rlib.unroll import unrolling_iterable

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

unrolling_types = unrolling_iterable(range(len(type_names)))

def lltype_for_name(name):
    """NOT_RPYTHON"""
    # XXX maybe use a dictionary
    return lltypes[type_names.index(name)]

def size_for_name(name):
    """NOT_RPYTHON"""
    # XXX maybe use a dictionary
    return lltype_sizes[type_names.index(name)]


class W_TypeObject(W_Object):
    classdef = ClassDef('Type', W_Object.classdef)

    typeindex = 0
    _immutable_fields_ = ['typeindex']

    def __init__(self, space, typeindex=0, klass=None):
        assert isinstance(typeindex, int)
        W_Object.__init__(self, space, klass)
        self.typeindex = typeindex

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        for i in range(len(ffi_types)):
            typename = type_names[i]
            w_new_type = W_BuiltinType(space, i)
            space.set_const(w_cls, typename, w_new_type)
            for alias in aliases[i]:
                space.set_const(w_cls, alias, w_new_type)
        space.set_const(w_cls, 'Mapped', space.getclassfor(W_MappedObject))

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_TypeObject(space, VOID)

    def __deepcopy__(self, memo):
        obj = super(W_TypeObject, self).__deepcopy__(memo)
        obj.typeindex = self.typeindex
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

class W_BuiltinType(W_TypeObject):
    classdef = ClassDef('Builtin', W_TypeObject.classdef)

    def __init__(self, space, typeindex):
        W_TypeObject.__init__(self, space, typeindex)

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        raise NotImplementedError

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

class W_StringType(W_BuiltinType):
    def __init__(self, space, klass=None):
        W_TypeObject.__init__(self, space, STRING)

    def read(self, space, data):
        typesize = lltype_sizes[self.typeindex]
        result = misc.read_raw_unsigned_data(data, typesize)
        result = rffi.cast(rffi.CCHARP, result)
        result = rffi.charp2str(result)
        return space.newstr_fromstr(result)

    def write(self, space, data, w_arg):
        typesize = lltype_sizes[self.typeindex]
        arg = space.str_w(w_arg)
        arg = rffi.str2charp(arg)
        arg = rffi.cast(lltype.Unsigned, arg)
        misc.write_raw_unsigned_data(data, arg, typesize)

class W_MappedObject(W_TypeObject):
    classdef = ClassDef('MappedObject', W_TypeObject.classdef)

    def __init__(self, space, klass=None):
        W_TypeObject.__init__(self, space, NATIVE_MAPPED)

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
        else:
            raise space.error(space.w_TypeError,
                              "native_type did not return instance of "
                              "FFI::Type")

    @classdef.method('to_native')
    def method_to_native(self, space, args_w):
        return space.send(self.w_data_converter, 'to_native', args_w)

    @classdef.method('from_native')
    def method_to_native(self, space, args_w):
        return space.send(self.w_data_converter, 'from_native', args_w)
