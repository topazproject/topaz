from __future__ import absolute_import

import os

from topaz.gateway import Coerce
from topaz.module import ModuleDef
from topaz.modules.signal import SIGNALS
from topaz.system import IS_WINDOWS
from topaz.error import error_for_oserror


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
    moduledef = ModuleDef("Process")

    @moduledef.function("euid")
    def method_euid(self, space):
        return space.newint(geteuid())

    @moduledef.function("pid")
    def method_pid(self, space):
        return space.newint(os.getpid())

    @moduledef.function("waitpid", pid="int")
    def method_waitpid(self, space, pid=-1):
        try:
            pid, status = os.waitpid(pid, 0)
        except OSError as e:
            raise error_for_oserror(space, e)
        status = WEXITSTATUS(status)
        w_status = space.send(
            space.find_const(self, "Status"),
            "new",
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
                space.send(self, "exit")
            else:
                return space.w_nil
        else:
            return space.newint(pid)

    @moduledef.function("kill")
    def method_kill(self, space, w_signal, args_w):
        if not args_w:
            raise space.error(space.w_ArgumentError,
                "wrong number of arguments (%d for at least 2)" % (len(args_w) + 1)
            )
        if space.is_kind_of(w_signal, space.w_fixnum):
            sig = space.int_w(w_signal)
        else:
            s = Coerce.str(space, w_signal)
            if s.startswith("SIG"):
                s = s[len("SIG"):]
            try:
                sig = SIGNALS[s]
            except KeyError:
                raise space.error(space.w_ArgumentError,
                    "unsupported name `SIG%s'" % s
                )

        if sig < 0:
            for w_arg in args_w:
                pid = space.int_w(w_arg)
                try:
                    os.killpg(pid, -sig)
                except OSError as e:
                    raise error_for_oserror(space, e)
        else:
            for w_arg in args_w:
                pid = space.int_w(w_arg)
                try:
                    os.kill(pid, sig)
                except OSError as e:
                    raise error_for_oserror(space, e)
        return space.newint(len(args_w))
