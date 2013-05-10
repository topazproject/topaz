from __future__ import absolute_import

from topaz.module import ModuleDef, ClassDef
from topaz.objects.objectobject import W_Object
from topaz.objects.exceptionobject import W_StandardError, new_exception_allocate

from rpython.rlib import clibffi, rarithmetic
from rpython.rtyper.lltypesystem import rffi

class FFI(object):
    moduledef = ModuleDef("FFI", filepath=__file__)

    @moduledef.setup_module
    def setup_module(space, w_mod):
        space.set_const(w_mod, 'TypeDefs', space.newhash())
        space.set_const(w_mod, 'Types', space.newhash())
        space.set_const(w_mod, 'Type', space.newclass('Type', None))

        md_DataConverter = ModuleDef('DataConverter', filepath=__file__)

        @md_DataConverter.function('native_type')
        def native_type(self, space, args_w): pass

        @md_DataConverter.function('to_native')
        def to_native(self, space): pass

        @md_DataConverter.function('from_native')
        def from_native(self, space): pass

        space.set_const(w_mod, 'DataConverter',
                        space.getmoduleobject(md_DataConverter))

        w_mapped = space.execute("""
                                 class Mapped
                                   def initialize(arg)
                                   end
                                 end
                                 Mapped
                                 """)

        w_type = space.find_const(w_mod, 'Type')
        space.set_const(w_type, 'Mapped', w_mapped)

        w_dynamic_lib = space.newclass('DynamicLibrary', None)
        space.set_const(w_mod, 'DynamicLibrary',
                        w_dynamic_lib)
        space.set_const(w_dynamic_lib, "RTLD_LAZY", space.w_nil)
        space.set_const(w_dynamic_lib, "RTLD_NOW", space.w_nil)
        space.set_const(w_dynamic_lib, "RTLD_GLOBAL", space.w_nil)
        space.set_const(w_dynamic_lib, "RTLD_LOCAL", space.w_nil)

        ffi_type_long = clibffi.cast_type_to_ffitype(rffi.LONG)
        ffi_type_ulong = clibffi.cast_type_to_ffitype(rffi.ULONG)
        ffitypes = {'VOID':clibffi.ffi_type_void,
                    'INT8': clibffi.ffi_type_sint8,
                    'UINT8': clibffi.ffi_type_uint8,
                    'INT16': clibffi.ffi_type_sint16,
                    'UINT16': clibffi.ffi_type_uint16,
                    'INT32': clibffi.ffi_type_sint32,
                    'UINT32': clibffi.ffi_type_uint32,
                    'INT64': clibffi.ffi_type_sint64,
                    'UINT64': clibffi.ffi_type_uint64,
                    'LONG': ffi_type_long,
                    'ULONG': ffi_type_ulong,
                    'FLOAT32': clibffi.ffi_type_float,
                    'FLOAT64': clibffi.ffi_type_double,
                    'LONGDOUBLE': clibffi.ffi_type_longdouble,
                    'POINTER': clibffi.ffi_type_pointer,
                    'BOOL': clibffi.ffi_type_uchar}
        typealiases = {'SCHAR': 'INT8', 'CHAR': 'INT8', 'UCHAR': 'UINT8',
                       'SHORT': 'INT16', 'SSHORT': 'INT16',
                       'USHORT': 'UINT16', 'INT': 'INT32', 'SINT': 'INT32',
                       'UINT': 'UINT32', 'LONG_LONG': 'INT64',
                       'SLONG': 'LONG', 'SLONG_LONG': 'INT64',
                       'ULONG_LONG': 'UINT64', 'FLOAT': 'FLOAT32',
                       'DOUBLE': 'FLOAT64', 'STRING': 'POINTER',
                       'BUFFER_IN': 'POINTER', 'BUFFER_OUT': 'POINTER',
                       'BUFFER_INOUT': 'POINTER', 'VARARGS': 'VOID'}
        w_ffi_type_cls = space.find_const(w_mod, 'Type')
        for typename in ffitypes:
            space.set_const(w_mod, 'TYPE_' + typename, space.w_nil)
            # using space.w_nil for now, should be something with
            # ffitypes[typename] later.
            space.set_const(w_ffi_type_cls, typename, space.w_nil)
        for aka in typealiases:
            ffitype = space.find_const(w_ffi_type_cls, typealiases[aka])
            space.set_const(w_ffi_type_cls, aka, ffitype)
