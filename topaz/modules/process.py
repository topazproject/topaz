from __future__ import absolute_import

import os

from topaz.module import Module, ModuleDef, ClassDef
from topaz.objects.objectobject import W_Object

class Process(Module):
    moduledef = ModuleDef("Process", filepath=__file__)

    @moduledef.setup_module
    def setup_module(space, w_mod):
        space.set_const(w_mod, "Status", space.w_process_status)

    @moduledef.function("euid")
    def method_euid(self, space):
        return space.newint(os.geteuid())

    @moduledef.function("pid")
    def method_pid(self, space):
        return space.newint(os.getpid())

    @moduledef.function("waitall")
    def method_waitall(self, space):
        raise space.error(space.w_NotImplementedError, "Process.waitall")

    @moduledef.function("wait")
    def method_wait(self, space):
        try:
            pid, status = os.waitpid(-1, 0)
            status = os.WEXITSTATUS(status)
            st = space.send(space.w_process_status,
                space.newsymbol("new"),
                [space.newint(pid), space.newint(status)])
            space.globals.set(space, "$?", st)
            return space.newint(pid)
        except OSError as ex:
            raise space.error(space.w_SystemCallError, str(ex))

    @moduledef.function("exit", status="int")
    def method_exit(self, space, status=0):
        raise space.error(space.w_SystemExit, "exit", [space.newint(status)])

    @moduledef.function("exit!", status="int")
    def method_exit_bang(self, space, status=0):
        os._exit(status)

    @moduledef.function("fork")
    def method_fork(self, space, block):
        pid = os.fork()
        if pid == 0:
            if block is not None:
                space.invoke_block(block, [])
                space.send(self, space.newsymbol("exit"))
            else:
                return space.w_nil
        else:
            return space.newint(pid)

class W_ProcessStatusObject(W_Object):
    classdef = ClassDef("Status", W_Object.classdef, filepath=__file__)

    classdef.app_method("""
    def initialize(pid, exitstatus)
      @pid = pid
      @exitstatus = exitstatus
    end

    def to_i
      @exitstatus
    end

    def pid
      @pid
    end
    """)
