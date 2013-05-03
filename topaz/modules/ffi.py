from __future__ import absolute_import

from topaz.module import ModuleDef, ClassDef
from topaz.objects.exceptionobject import W_StandardError, new_exception_allocate

from rpython.rlib import clibffi
from rpython.rtyper.lltypesystem import rffi

class FFI(object):
    moduledef = ModuleDef("FFI", filepath=__file__)

    @moduledef.function("call", name="str", arg="int")
    def method_call(self, space, name, arg):
        assert name == 'abs'
        clib = clibffi.CDLL(clibffi.get_libc_name())
        ptr = clib.getpointer(name, [clibffi.ffi_type_sint], clibffi.ffi_type_sint)
        ptr.push_arg(arg)
        res = ptr.call(rffi.INT)
        return space.newint(res)
