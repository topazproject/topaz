from __future__ import absolute_import

from rpython.rlib.rarithmetic import intmask

from topaz.module import Module, ModuleDef
from topaz.objects.classobject import W_ClassObject


class Topaz(Module):
    moduledef = ModuleDef("Topaz", filepath=__file__)

    @moduledef.function("intmask")
    def method_intmask(self, space, w_int):
        if space.is_kind_of(w_int, space.w_fixnum):
            return w_int
        elif space.is_kind_of(w_int, space.w_bignum):
            bigint = space.bigint_w(w_int)
            return space.newint(intmask(bigint.uintmask()))

    @moduledef.function("convert_type", method="symbol")
    def method_coerce_int(self, space, w_obj, w_type, method):
        if not isinstance(w_type, W_ClassObject):
            raise space.error(space.w_TypeError, "type argument must be a class")
        return space.convert_type(w_obj, w_type, method)

    @moduledef.function("compare")
    def method_compare(self, space, w_a, w_b, block=None):
        return space.compare(w_a, w_b, block)

