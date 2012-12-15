from rupypy.module import Module, ModuleDef


class Signal(Module):
    moduledef = ModuleDef("Signal")

    @moduledef.function("trap")
    def method_trap(self, args_w):
        pass
