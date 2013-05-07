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
        # TODO: LONG and ULONG ommited,
        #       since clibffi doesn't have slong or ulong
        typenames = ['VOID', 'INT8', 'UINT8', 'INT16', 'UINT16', 'INT32',
                     'UINT32', 'INT64', 'UINT64', 'FLOAT32',
                     'FLOAT64', 'LONGDOUBLE', 'POINTER', 'STRING', 'BUFFER_IN',
                     'BUFFER_OUT', 'BUFFER_INOUT', 'BOOL', 'VARARGS']
        ffitypes = ([clibffi.ffi_type_void, clibffi.ffi_type_sint8,
                     clibffi.ffi_type_uint8, clibffi.ffi_type_sint16,
                     clibffi.ffi_type_uint16, clibffi.ffi_type_sint32,
                     clibffi.ffi_type_uint32, clibffi.ffi_type_sint64,
                     clibffi.ffi_type_uint64, clibffi.ffi_type_float,
                     clibffi.ffi_type_double, clibffi.ffi_type_longdouble] +
                     4*[clibffi.ffi_type_pointer] +
                     [clibffi.ffi_type_uchar, clibffi.ffi_type_void])
        for tn in typenames:
            space.set_const(w_mod, 'TYPE_' + tn, space.w_nil)
        for tn, ft in zip(typenames, ffitypes):
            rbffi_type_class = space.find_const(w_mod, 'Type')
            space.set_const(rbffi_type_class, tn, space.w_nil)
