import os

from rupypy.module import Module, ModuleDef


class Kernel(Module):
    moduledef = ModuleDef("Kernel")

    @moduledef.function("class")
    def function_class(self, space):
        return space.getclass(self)

    @moduledef.function("puts")
    def function_puts(self, space, w_obj):
        if w_obj is space.w_nil:
            s = "nil"
        else:
            w_str = space.send(w_obj, space.newsymbol("to_s"))
            s = space.str_w(w_str)
        os.write(1, s)
        os.write(1, "\n")