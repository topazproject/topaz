from pypy.rlib.rarithmetic import intmask

from rupypy.module import Module, ModuleDef


class Topaz(Module):
    moduledef = ModuleDef("Topaz", filepath=__file__)

    @moduledef.function("intmask")
    def method_intmask(self, space, w_int):
        if space.is_kind_of(w_int, space.w_fixnum):
            return w_int
        elif space.is_kind_of(w_int, space.w_bignum):
            bigint = space.bigint_w(w_int)
            return space.newint(intmask(bigint.uintmask()))
