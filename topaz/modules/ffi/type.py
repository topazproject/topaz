from topaz.objects.objectobject import W_Object
from topaz.module import ClassDef

from rpython.rlib import clibffi
from rpython.rlib.rbigint import rbigint
from rpython.rtyper.lltypesystem import rffi
from rpython.rlib.rarithmetic import intmask

ffi_types = {'VOID':clibffi.ffi_type_void,
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
             'BOOL': clibffi.ffi_type_uchar,
             'VARARGS': clibffi.ffi_type_void}

native_types = {'VOID': rffi.VOIDP,
                'INT8': rffi.CHAR,
                'UINT8': rffi.UCHAR,
                'INT16': rffi.SHORT,
                'UINT16': rffi.USHORT,
                'INT32': rffi.INT,
                'UINT32': rffi.UINT,
                'LONG': rffi.LONG,
                'ULONG': rffi.ULONG,
                'INT64': rffi.LONGLONG,
                'UINT64': rffi.ULONGLONG,
                'FLOAT32': rffi.FLOAT,
                'FLOAT64': rffi.DOUBLE,
                'LONGDOUBLE': rffi.LONGDOUBLE,
                'POINTER': rffi.LONGLONG,
                'BOOL': rffi.CHAR,
                'VARARGS': rffi.CHAR}

aliases = {'SCHAR': 'INT8',
           'CHAR': 'INT8',
           'UCHAR': 'UINT8',
           'SHORT': 'INT16',
           'SSHORT': 'INT16',
           'USHORT': 'UINT16',
           'INT': 'INT32',
           'SINT': 'INT32',
           'UINT': 'UINT32',
           'LONG_LONG': 'INT64',
           'SLONG': 'LONG',
           'SLONG_LONG': 'INT64',
           'ULONG_LONG': 'UINT64',
           'FLOAT': 'FLOAT32',
           'DOUBLE': 'FLOAT64',
           'STRING': 'POINTER',
           'BUFFER_IN': 'POINTER',
           'BUFFER_OUT': 'POINTER',
           'BUFFER_INOUT': 'POINTER'}

class W_TypeObject(W_Object):
    classdef = ClassDef('Type', W_Object.classdef)

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        w_builtin = space.newclass('Builtin', w_cls)
        for typename in ffi_types:
            w_new_builtin_type = W_BuiltinObject(space, typename)
            space.set_const(w_cls, typename, w_new_builtin_type)
        for aka in aliases:
            w_new_type = W_TypeObject(space, aka)
            space.set_const(w_cls, aka, w_new_type)
        space.set_const(w_cls, 'Mapped', space.getclassfor(W_MappedObject))
        space.set_const(w_cls, 'Builtin', space.getclassfor(W_BuiltinObject))

    def __init__(self, space, name, klass=None):
        W_Object.__init__(self, space, klass)
        self.name = name

    def __deepcopy__(self, memo):
        obj = super(W_TypeObject, self).__deepcopy__(memo)
        obj.name = self.name
        return obj

    def __eq__(self, other):
        if not isinstance(other, W_TypeObject):
            return False
        return self.get_name() == other.get_name()

    def get_name(self):
        return aliases[self.name]

    def get_native_type(self):
        return native_types[self.get_name()]

    def get_ffi_type(self):
        return ffi_types[self.get_name()]

    def get_native_type(self):
        return native_types[self.name]

    @classdef.method('size')
    def method_size(self, space):
        r_uint_size = self.get_ffi_type().c_size
        size = intmask(r_uint_size)
        return space.newint(size)

class W_BuiltinObject(W_TypeObject):
    classdef = ClassDef('Builtin', W_TypeObject.classdef)

    def get_name(self):
        return self.name

class W_MappedObject(W_Object):
    classdef = ClassDef('MappedObject', W_Object.classdef)

    def __init__(self, space, klass=None):
        W_Object.__init__(self, space, klass)

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_MappedObject(space)

    @classdef.method('initialize')
    def method_initialize(self, space, args_w): pass
