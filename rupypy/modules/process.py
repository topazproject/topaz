import os

from rupypy.module import Module, ModuleDef
from rupypy.objects.exceptionobject import W_SystemExit


class Process(Module):
    moduledef = ModuleDef("Process")

    @moduledef.function("pid")
    def method_pid(self, space):
        return space.newint(os.getpid())

    @moduledef.function("exit")
    def method_exit(self, space, w_status=None):
        raise space.error(
            space.getclassfor(W_SystemExit),
            "exit",
            [w_status]
        )
