import os

from rupypy.module import Module, ModuleDef


class Process(Module):
    moduledef = ModuleDef("Process")

    @moduledef.function("pid")
    def method_pid(self, space):
        return space.newint(os.getpid())
