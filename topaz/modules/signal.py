from __future__ import absolute_import

from topaz.module import ModuleDef


class Signal(object):
    moduledef = ModuleDef("Signal")

    @moduledef.function("trap")
    def method_trap(self, args_w):
        pass
