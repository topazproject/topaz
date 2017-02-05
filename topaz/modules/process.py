from __future__ import absolute_import

import errno
import os

from rpython.rlib.rarithmetic import intmask
from rpython.rlib import rtime
from rpython.rtyper.lltypesystem import rffi, lltype

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

    def kill(pid, sig):
        raise NotImplementedError("kill on windows")

    def killpg(pid, sigs):
        raise OSError(errno.EINVAL, "group kill not available on windows")

    def WEXITSTATUS(status):
        return status
else:
    geteuid = os.geteuid
    fork = os.fork
    kill = os.kill
    killpg = os.killpg
    WEXITSTATUS = os.WEXITSTATUS


if not rtime.HAS_CLOCK_GETTIME:
    CLOCK_PROCESS_CPUTIME_ID = 1


class Process(object):
    moduledef = ModuleDef("Process")

    @moduledef.setup_module
    def setup_module(space, w_mod):
        if rtime.HAS_CLOCK_GETTIME:
            for name in rtime.ALL_DEFINED_CLOCKS:
                space.set_const(w_mod, name, space.newint(getattr(rtime, name)))
        else:
            space.set_const(
                w_mod,
                "CLOCK_PROCESS_CPUTIME_ID",
                CLOCK_PROCESS_CPUTIME_ID
            )

    @moduledef.function("euid")
    def method_euid(self, space):
        return space.newint(intmask(geteuid()))

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

    @moduledef.function("times")
    def method_times(self, space):
        tms = space.find_const(
            space.find_const(space.w_object, "Struct"),
            "Tms"
        )
        return space.send(
            tms,
            "new",
            [space.newfloat(t) for t in list(os.times()[0:4])]
        )

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
                pid = Coerce.int(space, w_arg)
                try:
                    killpg(pid, -sig)
                except OSError as e:
                    raise error_for_oserror(space, e)
        else:
            for w_arg in args_w:
                pid = Coerce.int(space, w_arg)
                try:
                    kill(pid, sig)
                except OSError as e:
                    raise error_for_oserror(space, e)
        return space.newint(len(args_w))

    @moduledef.function("clock_gettime", clockid="int")
    def method_clock_gettime(self, space, clockid, args_w):
        if len(args_w) > 1:
            raise space.error(space.w_ArgumentError,
                "wrong number of arguments (given %d, expected 1..2)"
            )
        if len(args_w) == 1:
            unit = Coerce.symbol(space, args_w[0])
        else:
            unit = "float_second"
        if rtime.HAS_CLOCK_GETTIME:
            with lltype.scoped_alloc(rtime.TIMESPEC) as a:
                if rtime.c_clock_gettime(clockid, a) == 0:
                    sec = rffi.getintfield(a, 'c_tv_sec')
                    nsec = rffi.getintfield(a, 'c_tv_nsec')
                else:
                    raise error_for_oserror(space, OSError(
                        errno.EINVAL, "clock_gettime")
                    )
        elif clockid == CLOCK_PROCESS_CPUTIME_ID:
            r = rtime.clock()
            sec = int(r)
            nsec = r * 1000000000
        else:
            raise error_for_oserror(space, OSError(
                errno.EINVAL, "clock_gettime")
            )
        if unit == "float_second":
            return space.newfloat(sec + nsec * 0.000000001)
        elif unit == "float_millisecond":
            return space.newfloat(sec * 1000 + nsec * 0.000001)
        elif unit == "float_microsecond":
            return space.newfloat(sec * 1000000 + nsec * 0.001)
        elif unit == "second":
            return space.newint(int(sec))
        elif unit == "millisecond":
            return space.newint(int(sec) * 1000)
        elif unit == "microsecond":
            return space.newint(sec * 1000000)
        elif unit == "nanosecond":
            return space.newint(sec * 1000000000 + nsec)
        else:
            raise space.error(space.w_ArgumentError,
                "unexpected unit: %s" % unit
            )
