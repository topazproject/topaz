import os

from pypy.rlib.rstring import assert_str0

from rupypy.module import Module, ModuleDef


class Kernel(Module):
    moduledef = ModuleDef("Kernel")

    @moduledef.method("class")
    def function_class(self, space):
        return space.getnonsingletonclass(self)

    @moduledef.method("lambda")
    def function_lambda(self, space, block):
        return space.newproc(block, True)

    @moduledef.function("puts")
    def function_puts(self, space, w_obj):
        if w_obj is space.w_nil:
            s = "nil"
        else:
            w_str = space.send(w_obj, space.newsymbol("to_s"))
            s = space.str_w(w_str)
        os.write(1, s)
        os.write(1, "\n")
        return space.w_nil

    @moduledef.function("require", path="path")
    def function_require(self, space, path):
        from pypy.rlib.streamio import open_file_as_stream

        from rupypy.objects.exceptionobject import W_LoadError

        assert path is not None
        orig_path = path
        if not path.endswith(".rb"):
            path += ".rb"

        if not (path.startswith("/") or path.startswith("./") or path.startswith("../")):
            w_load_path = space.globals.get("$LOAD_PATH")
            for w_base in space.listview(w_load_path):
                base = space.str_w(w_base)
                full = os.path.join(base, path)
                if os.path.exists(assert_str0(full)):
                    path = os.path.join(base, path)
                    break

        w_loaded_features = space.globals.get(space, '$"')
        w_already_loaded = space.send(
            w_loaded_features, space.newsymbol("include?"), [space.newstr_fromstr(orig_path)]
        )
        if space.is_true(w_already_loaded):
            return space.w_false

        if not os.path.exists(assert_str0(path)):
            space.raise_(space.getclassfor(W_LoadError), orig_path)

        f = open_file_as_stream(path)
        try:
            contents = f.readall()
        finally:
            f.close()

        w_loaded_features.method_lshift(space, space.newstr_fromstr(path))
        space.execute(contents, filepath=path)
        return space.w_true
