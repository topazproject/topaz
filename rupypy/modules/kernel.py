import os

from pypy.rlib.rstring import assert_str0

from rupypy.module import Module, ModuleDef


class Kernel(Module):
    moduledef = ModuleDef("Kernel")

    @moduledef.method("class")
    def function_class(self, space):
        return space.getclass(self)

    @moduledef.method("lambda")
    def function_lambda(self, space, block):
        return space.newproc(block, True)

    @moduledef.function("puts")
    def function_puts(self, ec, w_obj):
        if w_obj is ec.space.w_nil:
            s = "nil"
        else:
            w_str = ec.space.send(ec, w_obj, ec.space.newsymbol("to_s"))
            s = ec.space.str_w(w_str)
        os.write(1, s)
        os.write(1, "\n")

    @moduledef.function("require", path="path")
    def function_require(self, ec, path):
        from pypy.rlib.streamio import open_file_as_stream

        from rupypy.objects.exceptionobject import W_LoadError

        path = assert_str0(path)

        if not path.endswith(".rb"):
            path += ".rb"

        if not (path.startswith("/") or path.startswith("./") or path.startswith("../")):
            w_load_path = ec.space.globals.get(ec.space, "$LOAD_PATH")
            for w_base in ec.space.listview(w_load_path):
                base = ec.space.str_w(w_base)
                base = assert_str0(base)
                if os.path.exists(os.path.join(base, path)):
                    path = os.path.join(base, path)
                    break

        path = assert_str0(path)
        if not os.path.exists(path):
            ec.space.raise_(ec, ec.space.getclassfor(W_LoadError))

        f = open_file_as_stream(path)
        try:
            contents = f.readall()
        finally:
            f.close()

        ec.space.execute(ec, contents, filepath=path)
        return ec.space.w_true
