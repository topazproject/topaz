from __future__ import absolute_import

import math

from rpython.rlib import rfloat

from topaz.module import Module, ModuleDef


class Math(Module):
    moduledef = ModuleDef("Math", filepath=__file__)

    @moduledef.setup_module
    def setup_module(space, w_mod):
        space.set_const(w_mod, "PI", space.newfloat(math.pi))
        space.set_const(w_mod, "E", space.newfloat(math.e))
        space.set_const(w_mod, "DomainError", space.w_DomainError)

    @moduledef.function("exp", value="float")
    def method_exp(self, space, value):
        return space.newfloat(math.exp(value))

    @moduledef.function("sin", value="float")
    def method_sin(self, space, value):
        return space.newfloat(math.sin(value))

    @moduledef.function("sqrt", value="float")
    def method_sqrt(self, space, value):
        return space.newfloat(math.sqrt(value))

    @moduledef.function("log", value="float", base="float")
    def method_log(self, space, value, base=math.e):
        if base == math.e:
            return space.newfloat(math.log(value))
        else:
            return space.newfloat(math.log(value) / math.log(base))

    @moduledef.function("gamma", value="float")
    def method_gamma(self, space, value):
        try:
            res = rfloat.gamma(value)
        except ValueError:
            raise space.error(space.w_DomainError, 'Numerical argument is out of domain - "gamma"')
        except OverflowError:
            return space.newfloat(float('inf'))
        return space.newfloat(res)

