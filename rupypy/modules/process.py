import os

from rupypy.module import Module, ModuleDef
from rupypy.objects.exceptionobject import W_SystemExit


class Process(Module):
    moduledef = ModuleDef("Process")

    @moduledef.function("pid")
    def method_pid(self, space):
        return space.newint(os.getpid())

    @moduledef.function("exit", status="int")
    def method_exit(self, space, status=0):
        raise space.error(
            space.getclassfor(W_SystemExit),
            "exit",
            [space.newint(status)]
        )
