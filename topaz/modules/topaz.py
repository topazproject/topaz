from __future__ import absolute_import

from rpython.rlib.rarithmetic import intmask

from topaz.module import Module, ModuleDef, ClassDef
from topaz.objects.objectobject import W_Object


class Topaz(Module):
    moduledef = ModuleDef("Topaz", filepath=__file__)

    @moduledef.function("intmask")
    def method_intmask(self, space, w_int):
        if space.is_kind_of(w_int, space.w_fixnum):
            return w_int
        elif space.is_kind_of(w_int, space.w_bignum):
            bigint = space.bigint_w(w_int)
            return space.newint(intmask(bigint.uintmask()))


class W_Topaz_Type(W_Object):
    classdef = ClassDef("Type", W_Object.classdef, filepath=__file__)

    @classdef.singleton_method("convert_type", w_cls="class", method="symbol", raise_errors="bool")
    def method_convert_type(self, space, w_obj, w_cls, method, raise_errors):
        return space.convert_type(w_obj, w_cls, method, raise_errors)
