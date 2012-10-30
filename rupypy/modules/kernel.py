import os

from pypy.rlib.rstring import assert_str0
from pypy.rlib.streamio import open_file_as_stream

from rupypy.error import RubyError
from rupypy.module import Module, ModuleDef
from rupypy.modules.process import Process
from rupypy.objects.exceptionobject import W_ExceptionObject
from rupypy.objects.stringobject import W_StringObject


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
    def function_proc(self, space, block):
        return space.newproc(block, False)

    moduledef.app_method("""
    def puts *args
        $stdout.puts(*args)
    end
    """)

    moduledef.app_method("""
    def print *args
        $stdout.print(*args)
    end
    """)

    @staticmethod
    def find_feature(space, path):
        assert path is not None
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
        return path

    @staticmethod
    def load_feature(space, path, orig_path):
        if not os.path.exists(assert_str0(path)):
            raise space.error(space.w_LoadError, orig_path)

        f = open_file_as_stream(path)
        try:
            contents = f.readall()
        finally:
            f.close()

        space.execute(contents, filepath=path)

    @moduledef.function("require", path="path")
    def function_require(self, space, path):
        assert path is not None
        orig_path = path
        path = Kernel.find_feature(space, path)

        w_loaded_features = space.globals.get('$"')
        w_already_loaded = space.send(
            w_loaded_features, space.newsymbol("include?"), [space.newstr_fromstr(orig_path)]
        )
        if space.is_true(w_already_loaded):
            return space.w_false

        Kernel.load_feature(space, path, orig_path)
        w_loaded_features.method_lshift(space, space.newstr_fromstr(path))
        return space.w_true

    @moduledef.function("load", path="path")
    def function_load(self, space, path):
        assert path is not None
        orig_path = path
        path = Kernel.find_feature(space, path)
        Kernel.load_feature(space, path, orig_path)
        return space.w_true

    moduledef.app_method("alias fail raise")

    @moduledef.method("raise")
    def method_raise(self, space, w_str_or_exception=None, w_string=None, w_array=None):
        w_exception = None
        if w_str_or_exception is None:
            w_exception = space.globals.get("$!")
            if w_exception is space.w_nil:
                w_exception = space.w_RuntimeError
        elif isinstance(w_str_or_exception, W_StringObject):
            w_exception = space.w_RuntimeError
            w_string = w_str_or_exception
        else:
            w_exception = w_str_or_exception

        if not space.respond_to(w_exception, space.newsymbol("exception")):
            raise space.error(space.w_TypeError,
                "exception class/object expected"
            )

        if w_string is not None:
            w_exc = space.send(w_exception, space.newsymbol("exception"), [w_string])
        else:
            w_exc = space.send(w_exception, space.newsymbol("exception"))

        if w_array is not None:
            raise NotImplementedError("custom backtrace for Kernel#raise")

        if not isinstance(w_exc, W_ExceptionObject):
            raise space.error(space.w_TypeError,
                "exception object expected"
            )

        raise RubyError(w_exc)

    moduledef.app_method("""
    def Array arg
        if arg.respond_to? :to_ary
            arg.to_ary
        elsif arg.respond_to? :to_a
            arg.to_a
        else
            [arg]
        end
    end

    def String arg
        arg.to_s
    end
    module_function :String

    def Integer arg
        arg.to_i
    end
    module_function :Integer
    """)

    @moduledef.function("exit", status="int")
    def method_exit(self, space, status=0):
        return space.send(
            space.getmoduleobject(Process.moduledef),
            space.newsymbol("exit"),
            [space.newint(status)]
        )

    @moduledef.function("block_given?")
    @moduledef.function("iterator?")
    def method_block_givenp(self, space):
        return space.newbool(
            space.getexecutioncontext().gettopframe().get_block() is not None
        )

    @moduledef.function("exec")
    def method_exec(self, space, args_w):
        if len(args_w) > 1 and space.respond_to(args_w[0], space.newsymbol("to_hash")):
            raise space.error(space.w_NotImplementedError, "exec with environment")

        if len(args_w) > 1 and space.respond_to(args_w[-1], space.newsymbol("to_hash")):
            raise space.error(space.w_NotImplementedError, "exec with options")

        if space.respond_to(args_w[0], space.newsymbol("to_ary")):
            w_cmd = space.convert_type(args_w[0], space.w_array, "to_ary")
            cmd, argv0 = [
                space.str_w(space.convert_type(
                    w_e, space.w_string, "to_str"
                )) for w_e in space.listview(w_cmd)
            ]
        else:
            w_cmd = space.convert_type(args_w[0], space.w_string, "to_str")
            cmd = space.str_w(w_cmd)
            argv0 = None

        if len(args_w) > 1 or argv0 is not None:
            if argv0 is None:
                sepidx = cmd.rfind(os.sep) + 1
                if sepidx > 0:
                    argv0 = cmd[sepidx:]
                else:
                    argv0 = cmd
            args = [argv0]
            args += [
                space.str_w(space.convert_type(
                    w_arg, space.w_string, "to_str"
                )) for w_arg in args_w[1:]
            ]
            os.execv(cmd, args)
        else:
            shell = os.environ.get("RUBYSHELL") or os.environ.get("COMSPEC") or "/bin/sh"
            sepidx = shell.rfind(os.sep) + 1
            if sepidx > 0:
                argv0 = shell[sepidx:]
            else:
                argv0 = shell
            os.execv(shell, [argv0, "-c", cmd])

    @moduledef.function("at_exit")
    def method_at_exit(self, space, block):
        w_proc = space.newproc(block)
        space.register_exit_handler(w_proc)
        return w_proc

    @moduledef.function("=~")
    def method_match(self, space, w_other):
        return space.w_nil

    @moduledef.function("!~")
    def method_not_match(self, space, w_other):
        return space.newbool(not space.is_true(space.send(self, space.newsymbol("=~"), [w_other])))

    @moduledef.function("eql?")
    def method_eqlp(self, space, w_other):
        return space.newbool(self is w_other)

    @moduledef.function("instance_variable_defined?", name="symbol")
    def method_instance_variable_definedp(self, space, name):
        return space.newbool(self.find_instance_var(space, name) is not None)

    @moduledef.method("respond_to?")
    def method_respond_top(self, space, w_name):
        return space.newbool(space.respond_to(self, w_name))

    @moduledef.function("Float")
    def method_Float(self, space, w_arg):
        if w_arg is space.w_nil:
            raise space.error(space.w_TypeError, "can't convert nil into Float")
        elif space.is_kind_of(w_arg, space.w_numeric):
            return space.newfloat(space.float_w(w_arg))
        elif space.is_kind_of(w_arg, space.w_string):
            string = space.str_w(w_arg).strip(' ')
            try:
                return space.newfloat(float(string))
            except ValueError:
                raise space.error(space.w_ArgumentError, "invalid value for Float(): %s" % string)
        else:
            return space.convert_type(w_arg, space.w_float, "to_f")

    @moduledef.method("kind_of?")
    @moduledef.method("is_a?")
    def method_is_kind_ofp(self, space, w_mod):
        return space.newbool(self.is_kind_of(space, w_mod))

    @moduledef.method("instance_of?")
    def method_instance_of(self, space, w_mod):
        return space.newbool(space.getnonsingletonclass(self) is w_mod)
