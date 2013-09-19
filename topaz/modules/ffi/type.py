from topaz.objects.objectobject import W_Object
from topaz.module import ClassDef

from rpython.rlib import clibffi
from rpython.rlib.rbigint import rbigint
from rpython.rtyper.lltypesystem import rffi, lltype
from rpython.rlib.rarithmetic import intmask

typechars = {
    'VOID': 'v',
    'INT8': 'C',
    'UINT8': 'c',
    'INT16': 'S',
    'UINT16': 's',
    'INT32': 'I',
    'UINT32': 'i',
    'INT64': 'L',
    'UINT64': 'l',
    'LONG': 'W',
    'ULONG': 'w',
    'FLOAT32': 'f',
    'FLOAT64': 'd',
    'LONGDOUBLE': 'D',
    'POINTER': '>',
    'BOOL': '?',
    'VARARGS': '*',
    'STRING': '"'
}

ffi_types = {
                'VOID':clibffi.ffi_type_void,
                'INT8': clibffi.ffi_type_sint8,
                'UINT8': clibffi.ffi_type_uint8,
                'INT16': clibffi.ffi_type_sint16,
                'UINT16': clibffi.ffi_type_uint16,
                'INT32': clibffi.ffi_type_sint32,
                'UINT32': clibffi.ffi_type_uint32,
                'INT64': clibffi.ffi_type_sint64,
                'UINT64': clibffi.ffi_type_uint64,
                'LONG': clibffi.cast_type_to_ffitype(rffi.LONG),
                'ULONG': clibffi.cast_type_to_ffitype(rffi.ULONG),
                'FLOAT32': clibffi.ffi_type_float,
                'FLOAT64': clibffi.ffi_type_double,
                'LONGDOUBLE': clibffi.ffi_type_longdouble,
                'POINTER': clibffi.ffi_type_pointer,
                'BOOL': clibffi.cast_type_to_ffitype(lltype.Bool),
                'VARARGS': clibffi.ffi_type_void,
                'STRING': clibffi.ffi_type_pointer
            }

native_types = {
                'VOID': lltype.Void,
                'INT8': rffi.CHAR,
                'UINT8': rffi.UCHAR,
                'INT16': rffi.SHORT,
                'UINT16': rffi.USHORT,
                'INT32': rffi.INT,
                'UINT32': rffi.UINT,
                'INT64': rffi.LONGLONG,
                'UINT64': rffi.ULONGLONG,
                'LONG': rffi.LONG,
                'ULONG': rffi.ULONG,
                'FLOAT32': rffi.FLOAT,
                'FLOAT64': rffi.DOUBLE,
                'LONGDOUBLE': rffi.LONGDOUBLE,
                'POINTER': rffi.VOIDP,
                'BOOL': lltype.Bool,
                'VARARGS': rffi.CHAR,
                'STRING': rffi.CCHARP
               }

aliases = {
            'VOID': [],
            'INT8': ['CHAR', 'SCHAR'],
            'UINT8': ['UCHAR'],
            'INT16': ['SHORT', 'SSHORT'],
            'UINT16': ['USHORT'],
            'INT32': ['INT', 'SINT'],
            'UINT32': ['UINT'],
            'LONG': ['SLONG'],
            'ULONG': [],
            'INT64': ['LONG_LONG', 'SLONG_LONG'],
            'UINT64': ['ULONG_LONG'],
            'FLOAT32': ['FLOAT'],
            'FLOAT64': ['DOUBLE'],
            'LONGDOUBLE': [],
            'POINTER': ['BUFFER_IN', 'BUFFER_OUT', 'BUFFER_INOUT'],
            'BOOL': [],
            'VARARGS': [],
            'STRING': []
          }

class W_TypeObject(W_Object):
    classdef = ClassDef('Type', W_Object.classdef)

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        for typename in ffi_types:
            w_new_type = W_TypeObject(space, typename)
            space.set_const(w_cls, typename, w_new_type)
            for alias in aliases[typename]:
                space.set_const(w_cls, alias, w_new_type)
        space.set_const(w_cls, 'Mapped', space.getclassfor(W_MappedObject))

    def __init__(self, space, typename, klass=None):
        W_Object.__init__(self, space, klass)
        self.typename = typename

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_TypeObject(space, 'NEWTYPE')

    def __deepcopy__(self, memo):
        obj = super(W_TypeObject, self).__deepcopy__(memo)
        obj.typename = self.typename
        return obj

    def eq(self, w_other):
        if not isinstance(w_other, W_TypeObject):
            return False
        return self.typename == w_other.typename

    __eq__ = eq

    @classdef.method('==')
    def method_eq(self, space, w_other):
        return space.newbool(self.eq(w_other))

    @classdef.method('size')
    def method_size(self, space):
        r_uint_size = ffi_types[self.typename].c_size
        size = intmask(r_uint_size)
        return space.newint(size)

def type_object(space, w_obj):
    w_ffi_mod = space.find_const(space.w_kernel, 'FFI')
    w_type = space.send(w_ffi_mod, 'find_type', [w_obj])
    if not isinstance(w_type, W_TypeObject):
        raise space.error(space.w_TypeError,
                          "This seems to be a bug. find_type should always"
                           "return an FFI::Type object, but apparently it did"
                           "not in this case.")
    return w_type

class W_MappedObject(W_Object):
    classdef = ClassDef('MappedObject', W_Object.classdef)

    def __init__(self, space, klass=None):
        W_Object.__init__(self, space, klass)

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_MappedObject(space)

    @classdef.method('initialize')
    def method_initialize(self, space, args_w): pass
