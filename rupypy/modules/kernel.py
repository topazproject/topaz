import os

from rupypy.module import Module, ModuleDef


class Kernel(Module):
    moduledef = ModuleDef("Kernel")

    @moduledef.function("puts")
    def function_puts(self, space, w_obj):
        w_str = space.send(w_obj, space.newsymbol("to_s"))
        os.write(1, space.str_w(w_str))
        os.write(1, "\n")