from __future__ import absolute_import

import os

from topaz.module import ModuleDef
from topaz.system import IS_WINDOWS


if IS_WINDOWS:
    def geteuid():
        # MRI behaviour on windows
        return 0

    def fork():
        raise NotImplementedError("fork on windows")

    def WEXITSTATUS(status):
        return status
else:
    geteuid = os.geteuid
    fork = os.fork
    WEXITSTATUS = os.WEXITSTATUS


class Process(object):
    moduledef = ModuleDef("Process", filepath=__file__)

    @moduledef.function("euid")
    def method_euid(self, space):
        return space.newint(geteuid())

    @moduledef.function("pid")
    def method_pid(self, space):
        return space.newint(os.getpid())

    @moduledef.function("waitpid", pid="int")
    def method_waitpid(self, space, pid=-1):
        pid, status = os.waitpid(pid, 0)
        status = WEXITSTATUS(status)
        w_status = space.send(
            space.find_const(self, "Status"),
            space.newsymbol("new"),
            [space.newint(pid), space.newint(status)]
        )
        space.globals.set(space, "$?", w_status)
        return space.newint(pid)

    @moduledef.function("exit", status="int")
    def method_exit(self, space, status=0):
        raise space.error(space.w_SystemExit, "exit", [space.newint(status)])

    @moduledef.function("exit!", status="int")
    def method_exit_bang(self, space, status=0):
        os._exit(status)

    @moduledef.function("fork")
    def method_fork(self, space, block):
        pid = fork()
        if pid == 0:
            if block is not None:
                space.invoke_block(block, [])
                space.send(self, space.newsymbol("exit"))
            else:
                return space.w_nil
        else:
            return space.newint(pid)
