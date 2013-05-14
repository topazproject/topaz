from __future__ import absolute_import

from topaz.module import ModuleDef, ClassDef
from topaz.objects.objectobject import W_Object
from topaz.coerce import Coerce
from topaz.objects.exceptionobject import W_StandardError, new_exception_allocate

from rpython.rlib import clibffi, rarithmetic
from rpython.rtyper.lltypesystem import rffi

class DataConverter(object):
    moduledef = ModuleDef('DataConverter', filepath=__file__)

    @moduledef.function('native_type')
    def native_type(self, space, args_w): pass

    @moduledef.function('to_native')
    def to_native(self, space): pass

    @moduledef.function('from_native')
    def from_native(self, space): pass

class W_DynamicLibraryObject(W_Object):
    classdef = ClassDef('DynamicLibrary', W_Object.classdef, filepath=__file__)

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        space.set_const(w_cls, "RTLD_LAZY", space.newint(1))
        space.set_const(w_cls, "RTLD_NOW", space.newint(2))
        space.set_const(w_cls, "RTLD_GLOBAL", space.newint(257))
        space.set_const(w_cls, "RTLD_LOCAL", space.newint(0))

    @classdef.singleton_method('open', flags='int')
    def method_open(self, space, w_name, flags):
        if w_name == space.w_nil:
            name = None
        else:
            name = Coerce.path(space, w_name)
        return space.w_nil

class FFI(object):
    moduledef = ModuleDef("FFI", filepath=__file__)

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
             'BOOL': clibffi.ffi_type_uchar}
    aliases = {'SCHAR': 'INT8', 'CHAR': 'INT8', 'UCHAR': 'UINT8',
               'SHORT': 'INT16', 'SSHORT': 'INT16',
               'USHORT': 'UINT16', 'INT': 'INT32', 'SINT': 'INT32',
               'UINT': 'UINT32', 'LONG_LONG': 'INT64',
               'SLONG': 'LONG', 'SLONG_LONG': 'INT64',
               'ULONG_LONG': 'UINT64', 'FLOAT': 'FLOAT32',
               'DOUBLE': 'FLOAT64', 'STRING': 'POINTER',
               'BUFFER_IN': 'POINTER', 'BUFFER_OUT': 'POINTER',
               'BUFFER_INOUT': 'POINTER', 'VARARGS': 'VOID'}

    @moduledef.setup_module
    def setup_module(space, w_mod):
        # setup type constants
        space.set_const(w_mod, 'TypeDefs', space.newhash())
        space.set_const(w_mod, 'Types', space.newhash())
        for typename in FFI.types:
            space.set_const(w_mod, 'TYPE_' + typename, space.w_nil)

        # setup Type
        w_type = space.newclass('Type', None)
        for typename in FFI.types:
            # using space.w_nil for now, should be something with
            # FFI.types[typename] later.
            space.set_const(w_type, typename, space.w_nil)
        for aka in FFI.aliases:
            ffitype = space.find_const(w_type, FFI.aliases[aka])
            space.set_const(w_type, aka, ffitype)
        w_mapped = space.execute("""
                                 class Mapped
                                   def initialize(arg)
                                   end
                                 end
                                 Mapped
                                 """)
        space.set_const(w_type, 'Mapped', w_mapped)
        space.set_const(w_mod, 'Type', w_type)

        space.set_const(w_mod, 'DataConverter',
                        space.getmoduleobject(DataConverter.moduledef))

        # setup DynamicLibrary
        space.set_const(w_mod, 'DynamicLibrary',
                        space.getclassfor(W_DynamicLibraryObject))

        # setup Pointer
        w_pointer = space.newclass('Pointer', None)
        space.set_const(w_mod, 'Pointer', w_pointer)

        # setup Platform
        w_platform = space.newmodule('Platform', None)
        space.set_const(w_platform, 'ADDRESS_SIZE', space.newint(8))
        space.set_const(w_mod, 'Platform', w_platform)

        # setup StructLayout
        w_struct_layout = space.newclass('StructLayout', None)
        space.set_const(w_struct_layout, 'Field', space.w_nil)
        space.set_const(w_mod, 'StructLayout', w_struct_layout)

        # setup StructByReference
        w_struct_by_reference = space.newclass('StructByValue', None)
        space.set_const(w_mod, 'StructByReference', w_struct_by_reference)
