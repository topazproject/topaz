from pypy.tool.cache import Cache

from rupypy.executioncontext import ExecutionContext
from rupypy.gateway import WrapperGenerator


class ClassDef(object):
    def __init__(self, name, superclassdef=None):
        self.name = name
        self.methods = {}
        self.app_methods = []
        self.singleton_methods = {}
        self.superclassdef = superclassdef
        self.cls = None

    def _freeze_(self):
        return True

    def include_module(self, mod):
        self.methods.update(mod.moduledef.methods)
        self.app_methods.extend(mod.moduledef.app_methods)

    def method(self, name, **argspec):
        def adder(func):
            self.methods[name] = (func, argspec)
            return func
        return adder

    def app_method(self, source):
        self.app_methods.append(source)

    def singleton_method(self, name, **argspec):
        def adder(func):
            self.singleton_methods[name] = (func, argspec)
            return staticmethod(func)
        return adder

    def alias(self, target, alias):
        self.methods[alias] = self.methods[target]


class Module(object):
    @classmethod
    def build_object(cls, space):
        from rupypy.objects.functionobject import W_BuiltinFunction
        from rupypy.objects.moduleobject import W_ModuleObject

        w_mod = space.newmodule(cls.moduledef.name)
        for name, (method, argspec) in cls.moduledef.singleton_methods.iteritems():
            func = WrapperGenerator(name, method, argspec, W_ModuleObject).generate_wrapper()
            w_mod.attach_method(space, name, W_BuiltinFunction(name, func))
        return w_mod


class ModuleDef(object):
    def __init__(self, name):
        self.name = name
        self.methods = {}
        self.app_methods = []

        self.singleton_methods = {}
        self.singleton_add_methods = []

    def method(self, name, **argspec):
        def adder(func):
            self.methods[name] = (func, argspec)
        return adder

    def app_method(self, source):
        self.app_methods.append(source)

    def function(self, name, **argspec):
        def adder(func):
            # XXX: should be private, once we have visibility
            self.methods[name] = (func, argspec)
            self.singleton_methods[name] = (func, argspec)
        return adder


class ClassCache(Cache):
    def __init__(self, space):
        super(ClassCache, self).__init__()
        self.space = space

    def _build(self, classdef):
        from rupypy.objects.classobject import W_ClassObject
        from rupypy.objects.functionobject import W_BuiltinFunction

        assert classdef.cls is not None, classdef.name

        if classdef.superclassdef is None:
            superclass = None
        else:
            superclass = self.space.getclassobject(classdef.superclassdef)

        w_class = self.space.newclass(classdef.name, superclass)
        for name, (method, argspec) in classdef.methods.iteritems():
            func = WrapperGenerator(name, method, argspec, classdef.cls).generate_wrapper()
            w_class.define_method(self.space, name, W_BuiltinFunction(name, func))

        for source in classdef.app_methods:
            self.space.execute(ExecutionContext(self.space), source,
                w_self=w_class, w_scope=w_class
            )

        for name, (method, argspec) in classdef.singleton_methods.iteritems():
            func = WrapperGenerator(name, method, argspec, W_ClassObject).generate_wrapper()
            w_class.attach_method(self.space, name, W_BuiltinFunction(name, func))
        return w_class
