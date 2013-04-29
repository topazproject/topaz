from __future__ import absolute_import
import sys

from rpython.rlib.rarithmetic import intmask

from topaz.module import ModuleDef
from topaz.objects.classobject import W_ClassObject


class Topaz(object):
    moduledef = ModuleDef("Topaz", filepath=__file__)

    @moduledef.setup_module
    def setup_module(space, w_mod):
        space.set_const(w_mod, "FIXNUM_MAX", space.newint(sys.maxint))

    @moduledef.function("intmask")
    def method_intmask(self, space, w_int):
        if space.is_kind_of(w_int, space.w_fixnum):
            return w_int
        elif space.is_kind_of(w_int, space.w_bignum):
            bigint = space.bigint_w(w_int)
            return space.newint(intmask(bigint.uintmask()))

    @moduledef.function("convert_type", method="symbol")
    def method_convert_type(self, space, w_obj, w_type, method):
        if not isinstance(w_type, W_ClassObject):
            raise space.error(space.w_TypeError, "type argument must be a class")
        return space.convert_type(w_obj, w_type, method)

    @moduledef.function("compare")
    def method_compare(self, space, w_a, w_b, block=None):
        return space.compare(w_a, w_b, block)
