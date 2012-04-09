from pypy.tool.cache import Cache


def generate_wrapper(name, orig_func, argspec):
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
        elif argname != "self" and argname != "space":
            raise NotImplementedError(argname)
    source.append("    return func(self, space, *args)")

    source = "\n".join(source)
    namespace = {"func": orig_func}
    exec source in namespace
    return namespace[orig_func.__name__]


class ClassDef(object):
    def __init__(self, name):
        self.name = name
        self.methods = {}

    def include_module(self, mod):
        self.methods.update(mod.moduledef.methods)

    def method(self, name, **argspec):
        def adder(func):
            self.methods[name] = generate_wrapper(name, func, argspec)
        return adder


class Module(object):
    pass

class ModuleDef(object):
    def __init__(self, name):
        self.name = name
        self.methods = {}

    def function(self, name):
        def adder(func):
            self.methods[name] = generate_wrapper(name, func, ())
        return adder

class ClassCache(Cache):
    def __init__(self, space):
        super(ClassCache, self).__init__()
        self.space = space

    def _build(self, classdef):
        w_class = self.space.newclass(classdef.name)
        for name, method in classdef.methods.iteritems():
            w_class.add_method(name, method)
        return w_class