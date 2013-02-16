from __future__ import absolute_import

import os

from topaz.module import Module, ModuleDef


class Process(Module):
    moduledef = ModuleDef("Process", filepath=__file__)

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
            st = space.execute(
                "return Process::Status.new %i, %i" % (pid, status))
            space.globals.set(space, "$?", st)
            return space.newint(pid)
        except OSError as ex:
            raise space.error(space.w_SystemCallError, str(ex))

    @moduledef.function("exit", status="int")
    def method_exit(self, space, status=0):
        raise space.error(space.w_SystemExit, "exit", [space.newint(status)])

    @moduledef.function("exit!", status="int")
    def method_exit_bang(self, space, status=0):
        raise os._exit(status)

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

    moduledef.app_method("""
    class Status
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
    end
    """)
