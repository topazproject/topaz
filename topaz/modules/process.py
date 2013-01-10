from __future__ import absolute_import

import os

from topaz.module import Module, ModuleDef


class Process(Module):
    moduledef = ModuleDef("Process", filepath=__file__)

    @moduledef.function("pid")
    def method_pid(self, space):
        return space.newint(os.getpid())

    @moduledef.function("exit", status="int")
    def method_exit(self, space, status=0):
        raise space.error(space.w_SystemExit, "exit", [space.newint(status)])
