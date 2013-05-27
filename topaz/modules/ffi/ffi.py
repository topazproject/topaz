from __future__ import absolute_import

from topaz.module import ModuleDef, ClassDef
from topaz.objects.objectobject import W_Object
from topaz.objects.exceptionobject import W_StandardError, new_exception_allocate
from topaz.modules.ffi.dynamic_library import W_DynamicLibraryObject
from topaz.modules.ffi.pointer import W_PointerObject
from topaz.modules.ffi.data_converter import DataConverter

from rpython.rlib import clibffi, rarithmetic
from rpython.rtyper.lltypesystem import rffi

class FFI(object):
    moduledef = ModuleDef("FFI")

    types = {'VOID':clibffi.ffi_type_void,
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
    sizes = {'INT8': rffi.sizeof(rffi.CHAR),
             'INT16': rffi.sizeof(rffi.SHORT),
             'INT32': rffi.sizeof(rffi.INT),
             'INT64': rffi.sizeof(rffi.LONGLONG),
             'LONG': rffi.sizeof(rffi.LONG),
             'FLOAT': rffi.sizeof(rffi.FLOAT),
             'DOUBLE': rffi.sizeof(rffi.DOUBLE),
             'ADDRESS': rffi.sizeof(rffi.VOIDP)}

    @moduledef.setup_module
    def setup_module(space, w_mod):
        # setup type constants
        space.set_const(w_mod, 'TypeDefs', space.newhash())
        space.set_const(w_mod, 'Types', space.newhash())
        for typename in FFI.types:
            space.set_const(w_mod, 'TYPE_' + typename, space.w_nil)

        # setup NativeType
        w_native_type = space.newmodule('NativeType')
        for typename in FFI.types:
            space.set_const(w_native_type, typename, space.w_nil)
        space.set_const(w_mod, 'NativeType', w_native_type)

        # setup Type
        w_type = space.newclass('Type', None)
        w_builtin = space.newclass('Builtin', w_type)
        for typename in FFI.types:
            # using space.w_nil for now, should be something with
            # FFI.types[typename] later.
            space.set_const(w_type, typename, space.w_nil)
        for aka in FFI.aliases:
            ffitype = space.find_const(w_type, FFI.aliases[aka])
            space.set_const(w_type, aka, ffitype)
        space.set_const(w_type, 'Mapped', space.getclassfor(W_MappedObject))
        space.set_const(w_type, 'Builtin', w_builtin)
        space.set_const(w_mod, 'Type', w_type)

        space.set_const(w_mod, 'DataConverter',
                        space.getmoduleobject(DataConverter.moduledef))

        space.set_const(w_mod, 'DynamicLibrary',
                        space.getclassfor(W_DynamicLibraryObject))

        space.set_const(w_mod, 'Pointer',
                        space.getclassfor(W_PointerObject))

        # setup Platform
        w_platform = space.newmodule('Platform', None)
        for name in FFI.sizes:
            space.set_const(w_platform, name + '_SIZE',
                            space.newint(FFI.sizes[name]))
        space.set_const(w_mod, 'Platform', w_platform)

        # setup StructLayout
        w_struct_layout = space.newclass('StructLayout', None)
        space.set_const(w_struct_layout, 'Field', space.w_nil)
        space.set_const(w_mod, 'StructLayout', w_struct_layout)

        # setup StructByReference
        w_struct_by_reference = space.newclass('StructByValue', None)
        space.set_const(w_mod, 'StructByReference', w_struct_by_reference)

class W_MappedObject(W_Object):
    classdef = ClassDef('MappedObject', W_Object.classdef)

    def __init__(self, space, klass=None):
        W_Object.__init__(self, space, klass)

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_MappedObject(space)

    @classdef.method('initialize')
    def method_initialize(self, space, args_w): pass
