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

ffi_types['SCHAR'] == ffi_types['INT8']
ffi_types['CHAR'] == ffi_types['INT8']
ffi_types['UCHAR'] == ffi_types['UINT8']
ffi_types['SHORT'] == ffi_types['INT16']
ffi_types['SSHORT'] == ffi_types['INT16']
ffi_types['UHORT'] == ffi_types['UINT16']
ffi_types['INT'] == ffi_types['INT32']
ffi_types['SINT'] == ffi_types['INT32']
ffi_types['UINT'] == ffi_types['UINT32']
ffi_types['LONG_LONG'] == ffi_types['INT64']
ffi_types['SLONG'] == ffi_types['LONG']
ffi_types['SLONG_LONG'] == ffi_types['INT64']
ffi_types['ULONG_LONG'] == ffi_types['UINT64']
ffi_types['FLOAT'] == ffi_types['FLOAT32']
ffi_types['DOUBLE'] == ffi_types['FLOAT64']
ffi_types['STRING'] == ffi_types['POINTER']
ffi_types['BUFFER_IN'] == ffi_types['POINTER']
ffi_types['BUFFER_OUT'] == ffi_types['POINTER']
ffi_types['BUFFER_INOUT'] == ffi_types['POINTER']

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
                'POINTER': rffi.LONG,
                'BOOL': rffi.CHAR,
                'VARARGS': rffi.CHAR}

native_types['SCHAR'] == native_types['INT8']
native_types['CHAR'] == native_types['INT8']
native_types['UCHAR'] == native_types['UINT8']
native_types['SHORT'] == native_types['INT16']
native_types['SSHORT'] == native_types['INT16']
native_types['UHORT'] == native_types['UINT16']
native_types['INT'] == native_types['INT32']
native_types['SINT'] == native_types['INT32']
native_types['UINT'] == native_types['UINT32']
native_types['LONG_LONG'] == native_types['INT64']
native_types['SLONG'] == native_types['LONG']
native_types['SLONG_LONG'] == native_types['INT64']
native_types['ULONG_LONG'] == native_types['UINT64']
native_types['FLOAT'] == native_types['FLOAT32']
native_types['DOUBLE'] == native_types['FLOAT64']
native_types['STRING'] == native_types['POINTER']
native_types['BUFFER_IN'] == native_types['POINTER']
native_types['BUFFER_OUT'] == native_types['POINTER']
native_types['BUFFER_INOUT'] == native_types['POINTER']

#aliases = {'SCHAR': 'INT8',
#           'CHAR': 'INT8',
#           'UCHAR': 'UINT8',
#           'SHORT': 'INT16',
#           'SSHORT': 'INT16',
#           'USHORT': 'UINT16',
#           'INT': 'INT32',
#           'SINT': 'INT32',
#           'UINT': 'UINT32',
#           'LONG_LONG': 'INT64',
#           'SLONG': 'LONG',
#           'SLONG_LONG': 'INT64',
#           'ULONG_LONG': 'UINT64',
#           'FLOAT': 'FLOAT32',
#           'DOUBLE': 'FLOAT64',
#           'STRING': 'POINTER',
#           'BUFFER_IN': 'POINTER',
#           'BUFFER_OUT': 'POINTER',
#           'BUFFER_INOUT': 'POINTER'}

class W_TypeObject(W_Object):
    classdef = ClassDef('Type', W_Object.classdef)

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        w_builtin = space.newclass('Builtin', w_cls)
        for typename in ffi_types:
            w_new_builtin_type = W_BuiltinObject(space, typename)
            space.set_const(w_cls, typename, w_new_builtin_type)
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

    def get_native_type(self):
        return native_types[self.name]

    def get_ffi_type(self):
        return ffi_types[self.name]

    @classdef.method('size')
    def method_size(self, space):
        r_uint_size = self.get_ffi_type().c_size
        size = intmask(r_uint_size)
        return space.newint(size)

#class W_BuiltinObject(W_TypeObject):
#    classdef = ClassDef('Builtin', W_TypeObject.classdef)
#
#    def get_name(self):
#        return self.name

class W_MappedObject(W_Object):
    classdef = ClassDef('MappedObject', W_Object.classdef)

    def __init__(self, space, klass=None):
        W_Object.__init__(self, space, klass)

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_MappedObject(space)

    @classdef.method('initialize')
    def method_initialize(self, space, args_w): pass
