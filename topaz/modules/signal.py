from __future__ import absolute_import

from topaz.module import Module, ModuleDef


class Signal(Module):
    moduledef = ModuleDef("Signal", filepath=__file__)

    @moduledef.function("trap")
    def method_trap(self, args_w):
        pass
