import os

from pypy.rlib.rstring import assert_str0

from rupypy.module import Module, ModuleDef
from rupypy.objects.stringobject import W_StringObject
from rupypy.objects.exceptionobject import W_ExceptionObject, W_TypeError, W_RuntimeError
from rupypy.modules.process import Process
from rupypy.error import RubyError


class Kernel(Module):
    moduledef = ModuleDef("Kernel")

    @moduledef.method("class")
    def function_class(self, space):
        return space.getnonsingletonclass(self)

    @moduledef.method("singleton_methods", all="bool")
    def method_singleton_methods(self, space, all=True):
        methods = []
        w_cls = space.getclass(self)
        if w_cls.is_singleton:
            methods.extend(w_cls.methods_w.keys())
            w_cls = w_cls.superclass
        if all:
            while w_cls and w_cls.is_singleton:
                methods.extend(w_cls.methods_w.keys())
                w_cls = w_cls.superclass
        return space.newarray([space.newsymbol(m) for m in methods])

    @moduledef.method("lambda")
    def function_lambda(self, space, block):
        return space.newproc(block, True)

    @moduledef.method("proc")
    def function_lambda(self, space, block):
        return space.newproc(block, False)

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

        w_loaded_features = space.globals.get('$"')
        w_already_loaded = space.send(
            w_loaded_features, space.newsymbol("include?"), [space.newstr_fromstr(orig_path)]
        )
        if space.is_true(w_already_loaded):
            return space.w_false

        if not os.path.exists(assert_str0(path)):
            raise space.error(space.getclassfor(W_LoadError), orig_path)

        f = open_file_as_stream(path)
        try:
            contents = f.readall()
        finally:
            f.close()

        w_loaded_features.method_lshift(space, space.newstr_fromstr(path))
        space.execute(contents, filepath=path)
        return space.w_true

    moduledef.app_method("alias fail raise")

    @moduledef.method("raise")
    def method_raise(self, space, w_str_or_exception=None, w_string=None, w_array=None):
        w_exception = None
        if w_str_or_exception is None:
            w_exception = space.globals.get("$!")
            if w_exception is space.w_nil:
                w_exception = space.getclassfor(W_RuntimeError)
        elif isinstance(w_str_or_exception, W_StringObject):
            w_exception = space.getclassfor(W_RuntimeError)
            w_string = w_str_or_exception
        else:
            w_exception = w_str_or_exception

        if not space.respond_to(w_exception, space.newsymbol("exception")):
            raise space.error(space.getclassfor(W_TypeError),
                "exception class/object expected"
            )

        if w_string is not None:
            w_exc = space.send(w_exception, space.newsymbol("exception"), [w_string])
        else:
            w_exc = space.send(w_exception, space.newsymbol("exception"))

        if w_array is not None:
            raise NotImplementedError("custom backtrace for Kernel#raise")

        if not isinstance(w_exc, W_ExceptionObject):
            raise space.error(space.getclassfor(W_TypeError),
                "exception object expected"
            )

        raise RubyError(w_exc)

    @moduledef.method("Array")
    def method_Array(self, space, w_arg):
        if space.respond_to(w_arg, space.newsymbol("to_ary")):
            return space.send(w_arg, space.newsymbol("to_ary"))
        elif space.respond_to(w_arg, space.newsymbol("to_a")):
            return space.send(w_arg, space.newsymbol("to_a"))
        else:
            return space.newarray([w_arg])

    @moduledef.function("exit", status="int")
    def method_exit(self, space, status=0):
        return space.send(
            space.getmoduleobject(Process.moduledef),
            space.newsymbol("exit"),
            [space.newint(status)]
        )
