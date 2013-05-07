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
        ffi_type_long = clibffi.cast_type_to_ffitype(rffi.LONG)
        ffi_type_ulong = clibffi.cast_type_to_ffitype(rffi.ULONG)
        typenames = ['VOID', 'INT8', 'UINT8', 'INT16', 'UINT16', 'INT32',
                     'UINT32', 'INT64', 'UINT64', 'LONG', 'ULONG', 'FLOAT32',
                     'FLOAT64', 'LONGDOUBLE', 'POINTER', 'STRING', 'BUFFER_IN',
                     'BUFFER_OUT', 'BUFFER_INOUT', 'BOOL', 'VARARGS']
        ffitypes = ([clibffi.ffi_type_void, clibffi.ffi_type_sint8,
                     clibffi.ffi_type_uint8, clibffi.ffi_type_sint16,
                     clibffi.ffi_type_uint16, clibffi.ffi_type_sint32,
                     clibffi.ffi_type_uint32, clibffi.ffi_type_sint64,
                     clibffi.ffi_type_uint64, ffi_type_long, ffi_type_ulong,
                     clibffi.ffi_type_float, clibffi.ffi_type_double,
                     clibffi.ffi_type_longdouble] +
                     5*[clibffi.ffi_type_pointer] +
                     [clibffi.ffi_type_uchar, clibffi.ffi_type_void])
        assert len(typenames) == len(ffitypes)
        typealias = [('INT8', 'SCHAR'), ('INT8', 'CHAR'), ('UINT8', 'UCHAR'),
                     ('INT16', 'SHORT'), ('INT16', 'SSHORT'),
                     ('UINT16', 'USHORT'), ('INT32', 'INT'), ('INT32', 'SINT'),
                     ('UINT32', 'UINT'), ('INT64', 'LONG_LONG'),
                     ('LONG', 'SLONG'), ('INT64', 'SLONG_LONG'),
                     ('UINT64', 'ULONG_LONG'), ('FLOAT32', 'FLOAT'),
                     ('FLOAT64', 'DOUBLE')]
        for tn in typenames:
            space.set_const(w_mod, 'TYPE_' + tn, space.w_nil)
        rbffi_type_class = space.find_const(w_mod, 'Type')
        for tn, ft in zip(typenames, ffitypes):
            space.set_const(rbffi_type_class, tn, space.w_nil)
        for name, aka in typealias:
            ffitype = space.find_const(rbffi_type_class, name)
            space.set_const(rbffi_type_class, aka, ffitype)
