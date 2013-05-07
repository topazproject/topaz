from __future__ import absolute_import

from topaz.module import ModuleDef, ClassDef
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
        space.set_const(w_mod, 'DataConverter', space.newmodule('DataConverter'))
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
        rbffi_type_class = space.find_const(w_mod, 'Type')
        for typename in ffitypes:
            space.set_const(w_mod, 'TYPE_' + typename, space.w_nil)
            # using space.w_nil for now, should be something with
            # ffitypes[typename] later.
            space.set_const(rbffi_type_class, typename, space.w_nil)
        for aka in typealiases:
            ffitype = space.find_const(rbffi_type_class, typealiases[aka])
            space.set_const(rbffi_type_class, aka, ffitype)
