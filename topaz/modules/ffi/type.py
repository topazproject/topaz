from topaz.objects.objectobject import W_Object
from topaz.module import ClassDef

from rpython.rlib import clibffi
from rpython.rtyper.lltypesystem import rffi

class W_TypeObject(W_Object):
    classdef = ClassDef('Type', W_Object.classdef)

    basics = {'VOID':clibffi.ffi_type_void,
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
    aliases = {'SCHAR': 'INT8', 'CHAR': 'INT8', 'UCHAR': 'UINT8',
               'SHORT': 'INT16', 'SSHORT': 'INT16',
               'USHORT': 'UINT16', 'INT': 'INT32', 'SINT': 'INT32',
               'UINT': 'UINT32', 'LONG_LONG': 'INT64',
               'SLONG': 'LONG', 'SLONG_LONG': 'INT64',
               'ULONG_LONG': 'UINT64', 'FLOAT': 'FLOAT32',
               'DOUBLE': 'FLOAT64', 'STRING': 'POINTER',
               'BUFFER_IN': 'POINTER', 'BUFFER_OUT': 'POINTER',
               'BUFFER_INOUT': 'POINTER'}

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        w_builtin = space.newclass('Builtin', w_cls)
        for typename in W_TypeObject.basics:
            # using space.w_nil for now, should be something with
            # W_TypeObject.basics[typename] later.
            space.set_const(w_cls, typename, space.w_nil)
        for aka in W_TypeObject.aliases:
            ffitype = space.find_const(w_cls, W_TypeObject.aliases[aka])
            space.set_const(w_cls, aka, ffitype)
        space.set_const(w_cls, 'Mapped', space.getclassfor(W_MappedObject))
        space.set_const(w_cls, 'Builtin', w_builtin)

    def __init__(self, space, native_type, ffi_type, klass=None):
        W_Object.__init__(self, space, klass)
        self.native_type = native_type
        self.ffi_type = ffi_type

class W_MappedObject(W_Object):
    classdef = ClassDef('MappedObject', W_Object.classdef)

    def __init__(self, space, klass=None):
        W_Object.__init__(self, space, klass)

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_MappedObject(space)

    @classdef.method('initialize')
    def method_initialize(self, space, args_w): pass
