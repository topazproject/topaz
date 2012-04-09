import os
import sys

from rupypy.module import Module, ModuleDef


class Kernel(Module):
    moduledef = ModuleDef("Kernel")

    @moduledef.function("puts")
    def function_puts(self, space, w_obj):
        w_str = space.send(w_obj, space.newsymbol("to_s"))
        os.write(sys.stdout.fileno(), space.str_w(w_str))
        os.write(sys.stdout.fileno(), "\n")