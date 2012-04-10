from pypy.tool.cache import Cache


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
        elif argname != "space":
            raise NotImplementedError(argname)
    source.append("    return func(self, space, *args)")

    source = "\n".join(source)
    namespace = {"func": orig_func, "self_cls": self_cls}
    exec source in namespace
    return namespace[orig_func.__name__]


def finalize(cls):
    cls.classdef.cls = cls
    return cls

class ClassDef(object):
    def __init__(self, name):
        self.name = name
        self.methods = {}
        self.cls = None

    def _freeze_(self):
        return True

    def include_module(self, mod):
        self.methods.update(mod.moduledef.methods)

    def method(self, name, **argspec):
        def adder(func):
            self.methods[name] = (func, argspec)
        return adder


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

        w_class = self.space.newclass(classdef.name)
        for name, (method, argspec) in classdef.methods.iteritems():
            func = generate_wrapper(name, method, argspec, classdef.cls)
            w_class.add_method(name, func)
        return w_class