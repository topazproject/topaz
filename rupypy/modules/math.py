from __future__ import absolute_import

import math

from rupypy.module import Module, ModuleDef


class Math(Module):
    moduledef = ModuleDef("Math", filepath=__file__)

    @moduledef.setup_module
    def setup_module(space, w_mod):
        space.set_const(w_mod, "PI", space.newfloat(math.pi))

    @moduledef.function("exp", value="float")
    def method_exp(self, space, value):
        return space.newfloat(math.exp(value))

    @moduledef.function("sin", value="float")
    def method_sin(self, space, value):
        return space.newfloat(math.sin(value))

    @moduledef.function("sqrt", value="float")
    def method_sqrt(self, space, value):
        return space.newfloat(math.sqrt(value))
