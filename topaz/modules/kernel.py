from __future__ import absolute_import

import errno
import os
import time

from rpython.rlib.objectmodel import compute_identity_hash
from rpython.rlib.rfloat import round_double
from rpython.rlib.streamio import open_file_as_stream

from topaz.coerce import Coerce
from topaz.error import RubyError, error_for_oserror, error_for_errno
from topaz.module import ModuleDef, check_frozen
from topaz.modules.process import Process
from topaz.objects.bindingobject import W_BindingObject
from topaz.objects.exceptionobject import W_ExceptionObject
from topaz.objects.functionobject import W_FunctionObject
from topaz.objects.moduleobject import W_ModuleObject
from topaz.objects.procobject import W_ProcObject
from topaz.objects.randomobject import W_RandomObject
from topaz.objects.stringobject import W_StringObject
from topaz.scope import StaticScope


class Kernel(object):
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

    @moduledef.method("methods", inherit="bool")
    def method_methods(self, space, inherit=True):
        w_cls = space.getclass(self)
        return space.newarray([
            space.newsymbol(m)
            for m in w_cls.methods(space, inherit=inherit)
        ])

    @moduledef.method("private_methods", inherit="bool")
    def method_private_methods(self, space, inherit=True):
        w_cls = space.getclass(self)
        return space.newarray([
            space.newsymbol(m)
            for m in w_cls.methods(space, visibility=W_FunctionObject.PRIVATE, inherit=inherit)
        ])

    @moduledef.method("protected_methods", inherit="bool")
    def method_protected_methods(self, space, inherit=True):
        w_cls = space.getclass(self)
        return space.newarray([
            space.newsymbol(m)
            for m in w_cls.methods(space, visibility=W_FunctionObject.PROTECTED, inherit=inherit)
        ])

    @moduledef.method("public_methods", inherit="bool")
    def method_public_methods(self, space, inherit=True):
        w_cls = space.getclass(self)
        return space.newarray([
            space.newsymbol(m)
            for m in w_cls.methods(space, visibility=W_FunctionObject.PUBLIC, inherit=inherit)
        ])

    @moduledef.method("lambda")
    def function_lambda(self, space, block):
        if block is None:
            block = space.getexecutioncontext().gettoprubyframe().block
        if block is None:
            raise space.error(space.w_ArgumentError,
                "tried to create lambda object without a block"
            )
        else:
            return block.copy(space, is_lambda=True)

    @moduledef.method("proc")
    def function_proc(self, space, block):
        if block is None:
            block = space.getexecutioncontext().gettoprubyframe().block
        if block is None:
            raise space.error(space.w_ArgumentError,
                "tried to create Proc object without a block"
            )
        return block.copy(space)

    @staticmethod
    def find_feature(space, path):
        assert path is not None
        if os.path.isfile(path):
            return path
        if not path.endswith(".rb"):
            path += ".rb"

        if not (path.startswith("/") or path.startswith("./") or path.startswith("../")):
            w_load_path = space.globals.get(space, "$LOAD_PATH")
            for w_base in space.listview(w_load_path):
                base = Coerce.path(space, w_base)
                full = os.path.join(base, path)
                if os.path.isfile(full):
                    path = os.path.join(base, path)
                    break
        return path

    @staticmethod
    def load_feature(space, path, orig_path, wrap=False):
        if not os.path.exists(path):
            raise space.error(space.w_LoadError, orig_path)

        try:
            f = open_file_as_stream(path, buffering=0)
            try:
                contents = f.readall()
            finally:
                f.close()
        except OSError as e:
            raise error_for_oserror(space, e)

        if wrap:
            lexical_scope = StaticScope(space.newmodule("Anonymous"), None)
        else:
            lexical_scope = None
        space.execute(contents, filepath=path, lexical_scope=lexical_scope)

    @moduledef.function("require", path="path")
    def function_require(self, space, path):
        assert path is not None
        orig_path = path
        path = Kernel.find_feature(space, path)

        w_loaded_features = space.globals.get(space, '$"')
        w_already_loaded = space.send(
            w_loaded_features, "include?", [space.newstr_fromstr(path)]
        )
        if space.is_true(w_already_loaded):
            return space.w_false

        Kernel.load_feature(space, path, orig_path)
        w_loaded_features.method_lshift(space, space.newstr_fromstr(path))
        return space.w_true

    @moduledef.function("load", path="path", wrap="bool")
    def function_load(self, space, path, wrap=False):
        assert path is not None
        orig_path = path
        path = Kernel.find_feature(space, path)
        Kernel.load_feature(space, path, orig_path, wrap=wrap)
        return space.w_true

    @moduledef.method("fail")
    @moduledef.method("raise")
    def method_raise(self, space, w_str_or_exception=None, w_string=None, w_array=None):
        w_exception = None
        if w_str_or_exception is None:
            w_exception = space.globals.get(space, "$!") or space.w_nil
            if w_exception is space.w_nil:
                w_exception = space.w_RuntimeError
        elif isinstance(w_str_or_exception, W_StringObject):
            w_exception = space.w_RuntimeError
            w_string = w_str_or_exception
        else:
            w_exception = w_str_or_exception

        if not space.respond_to(w_exception, "exception"):
            raise space.error(space.w_TypeError,
                "exception class/object expected"
            )

        if w_string is not None:
            w_exc = space.send(w_exception, "exception", [w_string])
        else:
            w_exc = space.send(w_exception, "exception")

        if w_array is not None:
            raise space.error(
                space.w_NotImplementedError,
                "custom backtrace for Kernel#raise"
            )

        if not isinstance(w_exc, W_ExceptionObject):
            raise space.error(space.w_TypeError,
                "exception object expected"
            )

        raise RubyError(w_exc)

    @moduledef.function("exit")
    def method_exit(self, space, args_w):
        return space.send(
            space.getmoduleobject(Process.moduledef), "exit", args_w
        )

    @moduledef.function("exit!")
    def method_exit_bang(self, space, args_w):
        return space.send(
            space.getmoduleobject(Process.moduledef), "exit!", args_w
        )

    @moduledef.function("abort", msg="str")
    def method_abort(self, space, msg=None):
        if msg:
            os.write(2, msg)
        return space.send(self, "exit", [space.newint(1)])

    @moduledef.function("block_given?")
    @moduledef.function("iterator?")
    def method_block_givenp(self, space):
        return space.newbool(
            space.getexecutioncontext().gettoprubyframe().block is not None
        )

    @moduledef.function("binding")
    def method_binding(self, space):
        return space.newbinding_fromframe(space.getexecutioncontext().gettoprubyframe())

    @moduledef.function("__method__")
    @moduledef.function("__callee__")
    def method_callee(self, space):
        frame = space.getexecutioncontext().gettoprubyframe()
        return space.newsymbol(frame.bytecode.name)

    @moduledef.function("exec")
    def method_exec(self, space, args_w):
        if len(args_w) > 1 and space.respond_to(args_w[0], "to_hash"):
            raise space.error(space.w_NotImplementedError, "exec with environment")

        if len(args_w) > 1 and space.respond_to(args_w[-1], "to_hash"):
            raise space.error(space.w_NotImplementedError, "exec with options")

        if space.respond_to(args_w[0], "to_ary"):
            w_cmd = space.convert_type(args_w[0], space.w_array, "to_ary")
            cmd_w = space.listview(w_cmd)
            if len(cmd_w) != 2:
                raise space.error(space.w_ArgumentError, "wrong first argument")
            cmd, argv0 = [
                space.str0_w(space.convert_type(
                    w_e, space.w_string, "to_str"
                )) for w_e in cmd_w
            ]
        else:
            w_cmd = space.convert_type(args_w[0], space.w_string, "to_str")
            cmd = space.str0_w(w_cmd)
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
                space.str0_w(space.convert_type(
                    w_arg, space.w_string, "to_str"
                )) for w_arg in args_w[1:]
            ]
            try:
                os.execv(cmd, args)
            except OSError as e:
                raise error_for_oserror(space, e)
        else:
            if not cmd:
                raise error_for_errno(space, errno.ENOENT)
            shell = os.environ.get("RUBYSHELL") or os.environ.get("COMSPEC") or "/bin/sh"
            sepidx = shell.rfind(os.sep) + 1
            if sepidx > 0:
                argv0 = shell[sepidx:]
            else:
                argv0 = shell
            try:
                os.execv(shell, [argv0, "-c", cmd])
            except OSError as e:
                raise error_for_oserror(space, e)

    @moduledef.function("system")
    def method_system(self, space, args_w):
        raise space.error(space.w_NotImplementedError, "Kernel#system()")

    @moduledef.function("fork")
    def method_fork(self, space, block):
        return space.send(
            space.getmoduleobject(Process.moduledef), "fork", block=block
        )

    @moduledef.function("at_exit")
    def method_at_exit(self, space, block):
        space.register_exit_handler(block)
        return block

    @moduledef.function("=~")
    def method_match(self, space, w_other):
        return space.w_nil

    @moduledef.function("!~")
    def method_not_match(self, space, w_other):
        return space.newbool(not space.is_true(space.send(self, "=~", [w_other])))

    @moduledef.function("eql?")
    def method_eqlp(self, space, w_other):
        return space.newbool(self is w_other)

    @moduledef.function("instance_variable_defined?", name="symbol")
    def method_instance_variable_definedp(self, space, name):
        return space.newbool(self.find_instance_var(space, name) is not None)

    @moduledef.method("respond_to?", include_private="bool")
    def method_respond_top(self, space, w_name, include_private=False):
        if space.respond_to(self, space.symbol_w(w_name)):
            return space.newbool(True)

        w_found = space.send(
            self,
            "respond_to_missing?",
            [w_name, space.newbool(include_private)]
        )
        return space.newbool(space.is_true(w_found))

    @moduledef.method("respond_to_missing?")
    def method_respond_to_missingp(self, space, w_name, w_include_private):
        return space.newbool(False)

    @moduledef.method("dup")
    def method_dup(self, space):
        if (self is space.w_nil or self is space.w_true or
            self is space.w_false or space.is_kind_of(self, space.w_symbol) or
            space.is_kind_of(self, space.w_fixnum)):
            raise space.error(space.w_TypeError, "can't dup %s" % space.getclass(self).name)
        w_dup = space.send(space.getnonsingletonclass(self), "allocate")
        w_dup.copy_instance_vars(space, self)
        space.infect(w_dup, self, freeze=False)
        space.send(w_dup, "initialize_dup", [self])
        return w_dup

    @moduledef.method("clone")
    def method_clone(self, space):
        if (self is space.w_nil or self is space.w_true or
            self is space.w_false or space.is_kind_of(self, space.w_symbol) or
            space.is_kind_of(self, space.w_fixnum)):
            raise space.error(space.w_TypeError, "can't dup %s" % space.getclass(self).name)
        w_dup = space.send(space.getnonsingletonclass(self), "allocate")
        w_dup.copy_instance_vars(space, self)
        w_dup.copy_singletonclass(space, space.getsingletonclass(self))
        space.send(w_dup, "initialize_clone", [self])
        space.infect(w_dup, self, freeze=True)
        return w_dup

    @moduledef.method("sleep")
    def method_sleep(self, space, w_duration=None):
        if w_duration is None:
            raise space.error(space.w_NotImplementedError)
        elif space.is_kind_of(w_duration, space.w_string):
            raise space.error(space.w_TypeError, "can't convert String into time interval")
        start = time.time()
        time.sleep(Coerce.float(space, w_duration))
        return space.newint(int(round_double(time.time() - start, 0)))

    @moduledef.method("initialize_clone")
    @moduledef.method("initialize_dup")
    def method_initialize_dup(self, space, w_other):
        space.send(self, "initialize_copy", [w_other])
        return self

    @moduledef.method("initialize_copy")
    def method_initialize_copy(self, space, w_other):
        return self

    @moduledef.function("Float")
    def method_Float(self, space, w_arg):
        if w_arg is space.w_nil:
            raise space.error(space.w_TypeError, "can't convert nil into Float")
        elif space.is_kind_of(w_arg, space.w_float):
            return space.newfloat(space.float_w(w_arg))
        elif space.is_kind_of(w_arg, space.w_string):
            string = space.str_w(w_arg).strip(" ")
            try:
                return space.newfloat(float(string))
            except ValueError:
                raise space.error(space.w_ArgumentError, "invalid value for Float(): %s" % string)
        else:
            return space.convert_type(w_arg, space.w_float, "to_f")

    @moduledef.method("kind_of?")
    @moduledef.method("is_a?")
    def method_is_kind_ofp(self, space, w_mod):
        if not isinstance(w_mod, W_ModuleObject):
            raise space.error(space.w_TypeError, "class or module required")
        return space.newbool(self.is_kind_of(space, w_mod))

    @moduledef.method("instance_of?")
    def method_instance_of(self, space, w_mod):
        if not isinstance(w_mod, W_ModuleObject):
            raise space.error(space.w_TypeError, "class or module required")
        return space.newbool(space.getnonsingletonclass(self) is w_mod)

    @moduledef.method("eval")
    def method_eval(self, space, w_source, w_binding=None):
        if w_binding is None:
            frame = space.getexecutioncontext().gettoprubyframe()
            w_binding = space.newbinding_fromframe(frame)
        elif not isinstance(w_binding, W_BindingObject):
            raise space.error(space.w_TypeError,
                "wrong argument type %s (expected Binding)" % space.getclass(w_binding).name
            )
        return space.send(w_binding, "eval", [w_source])

    @moduledef.method("set_trace_func")
    def method_set_trace_func(self, space, w_proc):
        if w_proc is space.w_nil:
            w_proc = None
        else:
            assert isinstance(w_proc, W_ProcObject)
        space.getexecutioncontext().settraceproc(w_proc)

    def new_flag(moduledef, setter, getter, remover):
        @moduledef.method(setter)
        def setter_method(self, space):
            self.set_flag(space, getter)
            return self

        @moduledef.method(getter)
        def getter_method(self, space):
            return self.get_flag(space, getter)

        if remover is None:
            return (setter_method, getter_method)
        else:
            @moduledef.method(remover)
            def remover_method(self, space):
                self.unset_flag(space, getter)
                return self
            return (setter_method, getter_method, remover_method)
    method_untrust, method_untrusted, method_trust = new_flag(moduledef, "untrust", "untrusted?", "trust")
    method_taint, method_tainted, method_untaint = new_flag(moduledef, "taint", "tainted?", "untaint")
    method_freeze, method_frozen = new_flag(moduledef, "freeze", "frozen?", None)

    @moduledef.method("throw", name="symbol")
    def method_throw(self, space, name, w_value=None):
        from topaz.interpreter import Throw
        if not space.getexecutioncontext().is_in_catch_block_for_name(name):
            raise space.error(space.w_ArgumentError, "uncaught throw :%s" % name)
        if w_value is None:
            w_value = space.w_nil
        raise Throw(name, w_value)

    @moduledef.method("catch", name="symbol")
    def method_catch(self, space, name, block):
        if block is None:
            raise space.error(space.w_LocalJumpError, "no block given")
        from topaz.interpreter import Throw
        with space.getexecutioncontext().catch_block(name):
            try:
                return space.invoke_block(block, [])
            except Throw as e:
                if e.name == name:
                    return e.w_value
                raise

    @moduledef.method("srand")
    def method_srand(self, space, w_seed=None):
        random_class = space.getclassfor(W_RandomObject)
        default = space.find_const(random_class, "DEFAULT")
        return default.srand(space, w_seed)

    @moduledef.method("autoload")
    def method_autoload(self, space, args_w):
        return space.send(space.getclass(self), "autoload", args_w)

    @moduledef.method("autoload?")
    def method_autoload(self, space, args_w):
        return space.send(space.getclass(self), "autoload?", args_w)

    @moduledef.method("object_id")
    def method_object_id(self, space):
        return space.send(self, "__id__")

    @moduledef.method("singleton_class")
    def method_singleton_class(self, space):
        return space.getsingletonclass(self)

    @moduledef.method("extend")
    @check_frozen()
    def method_extend(self, space, w_mod):
        if not space.is_kind_of(w_mod, space.w_module) or space.is_kind_of(w_mod, space.w_class):
            if space.is_kind_of(w_mod, space.w_class):
                name = "Class"
            else:
                name = space.obj_to_s(space.getclass(w_mod))
            raise space.error(
                space.w_TypeError,
                "wrong argument type %s (expected Module)" % name
            )
        space.send(w_mod, "extend_object", [self])
        space.send(w_mod, "extended", [self])

    @moduledef.method("inspect")
    def method_inspect(self, space):
        return space.send(self, "to_s")

    @moduledef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr(space.any_to_s(self))

    @moduledef.method("===")
    def method_eqeqeq(self, space, w_other):
        if self is w_other:
            return space.w_true
        return space.send(self, "==", [w_other])

    @moduledef.method("send")
    def method_send(self, space, args_w, block):
        return space.send(self, "__send__", args_w, block)

    @moduledef.method("nil?")
    def method_nilp(self, space):
        return space.w_false

    @moduledef.method("hash")
    def method_hash(self, space):
        return space.newint(compute_identity_hash(self))

    @moduledef.method("instance_variable_get", name="str")
    def method_instance_variable_get(self, space, name):
        return space.find_instance_var(self, name)

    @moduledef.method("instance_variable_set", name="str")
    @check_frozen()
    def method_instance_variable_set(self, space, name, w_value):
        space.set_instance_var(self, name, w_value)
        return w_value

    @moduledef.method("method")
    def method_method(self, space, w_sym):
        return space.send(
            space.send(space.getclass(self), "instance_method", [w_sym]),
            "bind",
            [self]
        )

    @moduledef.method("tap")
    def method_tap(self, space, block):
        if block is not None:
            space.invoke_block(block, [self])
        else:
            raise space.error(space.w_LocalJumpError, "no block given")
        return self

    @moduledef.method("define_singleton_method", name="symbol")
    @check_frozen()
    def method_define_singleton_method(self, space, name, w_method=None, block=None):
        args_w = [space.newsymbol(name)]
        if w_method is not None:
            args_w.append(w_method)
        return space.send(space.getsingletonclass(self), "define_method", args_w, block)
