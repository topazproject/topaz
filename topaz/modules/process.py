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

    @moduledef.function("fork")
    def method_fork(self, space, block):
        pid = os.fork()
        if pid == 0:
            if block is not None:
                space.invoke_block(block, [])
                exit(0)
            else:
                return space.w_nil
        return space.newint(pid)
