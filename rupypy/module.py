from pypy.rlib import jit
from pypy.tool.cache import Cache

from rupypy.interpreter import Interpreter, Frame


def generate_wrapper(name, orig_func, argspec, self_cls):
    source = []
    source.append("def %s(self, space, args_w):" % orig_func.__name__)
    source.append("    args = ()")
    code = orig_func.__code__
    arg_count = 0
    for i, argname in enumerate(code.co_varnames[:code.co_argcount]):
        if argname in argspec:
            spec = argspec[argname]
            if spec is int:
                source.append("    args += (space.int_w(args_w[%d]),)" % arg_count)
            else:
                raise NotImplementedError(spec)
            arg_count += 1
        elif argname.startswith("w_"):
            source.append("    args += (args_w[%d],)" % arg_count)
            arg_count += 1
        elif argname == "self":
            source.append("    assert isinstance(self, self_cls)")
        elif argname == "args_w":
            source.append("    args += (args_w,)")
        elif argname != "space":
            raise NotImplementedError(argname)
    source.append("    return func(self, space, *args)")

    source = "\n".join(source)
    namespace = {"func": orig_func, "self_cls": self_cls}
    exec source in namespace
    return namespace[orig_func.__name__]


class ClassDef(object):
    def __init__(self, name, superclassdef=None):
        self.name = name
        self.methods = {}
        self.app_methods = []
        self.superclassdef = superclassdef
        self.cls = None

    def _freeze_(self):
        return True

    def include_module(self, mod):
        self.methods.update(mod.moduledef.methods)

    def method(self, name, **argspec):
        def adder(func):
            self.methods[name] = (func, argspec)
            return func
        return adder

    def app_method(self, source):
        self.app_methods.append(source)

class Module(object):
    pass

class ModuleDef(object):
    def __init__(self, name):
        self.name = name
        self.methods = {}

    def function(self, name, **argspec):
        def adder(func):
            self.methods[name] = (func, argspec)
        return adder

class ClassCache(Cache):
    def __init__(self, space):
        super(ClassCache, self).__init__()
        self.space = space

    def _build(self, classdef):
        assert classdef.cls is not None, classdef.name

        if classdef.superclassdef is None:
            superclass = None
        else:
            superclass = self.space.getclassobject(classdef.superclassdef)

        w_class = self.space.newclass(classdef.name, superclass)
        for name, (method, argspec) in classdef.methods.iteritems():
            func = generate_wrapper(name, method, argspec, classdef.cls)
            w_class.add_method(self.space, name, BuiltinFunction(func))
        for source in classdef.app_methods:
            self.space.execute(source, w_class)
        return w_class

class BaseFunction(object):
    pass

class Function(BaseFunction):
    _immutable_fields_ = ["bytecode"]

    def __init__(self, name, bytecode):
        self.name = name
        self.bytecode = bytecode

    @jit.unroll_safe
    def call(self, space, w_receiver, args_w):
        from rupypy.objects.objectobject import W_Object
        # XXX: is scope right?
        frame = Frame(self.bytecode, w_receiver, space.getclassfor(W_Object))
        # XXX arg count checking
        for i, w_arg in enumerate(args_w):
            frame.locals_w[i] = w_arg
        return Interpreter().interpret(space, frame, self.bytecode)

class BuiltinFunction(BaseFunction):
    _immutable_fields_ = ["func"]

    def __init__(self, func):
        self.func = func

    def call(self, space, w_receiver, args_w):
        return self.func(w_receiver, space, args_w)