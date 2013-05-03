from __future__ import absolute_import

from topaz.module import ModuleDef, ClassDef
from topaz.objects.exceptionobject import W_StandardError, new_exception_allocate

from rpython.rlib import clibffi, rarithmetic
from rpython.rtyper.lltypesystem import rffi

class FFI(object):
    moduledef = ModuleDef("FFI", filepath=__file__)

    @moduledef.function("call", name="str")
    def method_call(self, space, name, w_args):
        assert name == 'abs' or 'ceil'
        lib = (clibffi.CDLL('libm.so') if name == 'ceil' else
               clibffi.CDLL(clibffi.get_libc_name()))
        if space.is_kind_of(w_args, space.w_integer):
            arg = space.int_w(w_args)
            arg_type = clibffi.ffi_type_sint
            rffi_type = rffi.INT
        elif space.is_kind_of(w_args, space.w_float):
            arg = space.float_w(w_args)
            arg_type = clibffi.ffi_type_double
            rffi_type = rffi.DOUBLE
        else:
            raise Exception("not supported")
        ptr = lib.getpointer(name, [arg_type], arg_type)
        ptr.push_arg(arg)
        res = ptr.call(rffi_type)
        #if isinstance(res, rarithmetic.r_int):
        if name == 'abs':
            return space.newint(res)
        elif name == 'ceil':
        #elif isinstance(res, rarithmetic.r_singlefloat):
            return space.newfloat(res)
        else:
            raise Exception("not supported")
