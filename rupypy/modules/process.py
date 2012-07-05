import os

from rupypy.error import RubyError
from rupypy.module import Module, ModuleDef
from rupypy.objects.exceptionobject import W_SystemExit


class Process(Module):
    moduledef = ModuleDef("Process")

    @moduledef.function("pid")
    def method_pid(self, space):
        return space.newint(os.getpid())

    @moduledef.function("exit")
    def method_exit(self, space, w_status=None):
        w_exc = space.send(
            space.getclassfor(W_SystemExit),
            space.newsymbol("new"),
            [space.newstr_fromstr("exit"), w_status]
        )
        assert isinstance(w_exc, W_SystemExit)
        raise RubyError(w_exc)
