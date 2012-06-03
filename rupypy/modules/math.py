from __future__ import absolute_import

import math

from rupypy.module import Module, ModuleDef


class Math(Module):
    moduledef = ModuleDef("Math")

    @moduledef.function("exp", value="float")
    def method_exp(self, space, value):
        return space.newfloat(math.exp(value))

    @moduledef.function("sin", value="float")
    def method_sin(self, space, value):
        return space.newfloat(math.sin(value))
