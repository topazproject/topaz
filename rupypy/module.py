from rupypy.gateway import WrapperGenerator
from rupypy.utils.cache import Cache


class ClassDef(object):
    def __init__(self, name, superclassdef=None):
        self.name = name
        self.methods = {}
        self.app_methods = []
        self.singleton_methods = {}
        self.includes = []
        self.superclassdef = superclassdef
        self.cls = None

    def __repr__(self):
        return "<ClassDef: {}>".format(self.name)

    def __deepcopy__(self, memo):
        return self

    def _freeze_(self):
        return True

    def include_module(self, mod):
        self.includes.append(mod)

    def method(self, __name, **argspec):
        name = __name

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


class Module(object):
    pass


class ModuleDef(object):
    def __init__(self, name):
        self.name = name
        self.methods = {}
        self.app_methods = []

        self.singleton_methods = {}

    def __deepcopy__(self, memo):
        return self

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
    def _build(self, classdef):
        from rupypy.objects.classobject import W_ClassObject
        from rupypy.objects.functionobject import W_BuiltinFunction

        assert classdef.cls is not None, classdef.name

        if classdef.superclassdef is None:
            superclass = None
        else:
            superclass = self.space.getclassobject(classdef.superclassdef)

        w_class = self.space.newclass(classdef.name, superclass)
        yield w_class
        for name, (method, argspec) in classdef.methods.iteritems():
            func = WrapperGenerator(name, method, argspec, classdef.cls).generate_wrapper()
            w_class.define_method(self.space, name, W_BuiltinFunction(name, func))

        for source in classdef.app_methods:
            self.space.execute(source, w_self=w_class, w_scope=w_class)

        for name, (method, argspec) in classdef.singleton_methods.iteritems():
            func = WrapperGenerator(name, method, argspec, W_ClassObject).generate_wrapper()
            w_class.attach_method(self.space, name, W_BuiltinFunction(name, func))

        for mod in reversed(classdef.includes):
            w_mod = self.space.getmoduleobject(mod.moduledef)
            self.space.send(w_class, self.space.newsymbol("include"), [w_mod])

        classdef.cls.setup_class(self.space, w_class)


class ModuleCache(Cache):
    def _build(self, moduledef):
        from rupypy.objects.functionobject import W_BuiltinFunction
        from rupypy.objects.moduleobject import W_ModuleObject
        from rupypy.objects.objectobject import W_BaseObject

        w_mod = self.space.newmodule(moduledef.name)
        for name, (method, argspec) in moduledef.methods.iteritems():
            func = WrapperGenerator(name, method, argspec, W_BaseObject).generate_wrapper()
            w_mod.define_method(self.space, name, W_BuiltinFunction(name, func))
        for source in moduledef.app_methods:
            self.space.execute(source, w_self=w_mod, w_scope=w_mod)
        for name, (method, argspec) in moduledef.singleton_methods.iteritems():
            func = WrapperGenerator(name, method, argspec, W_ModuleObject).generate_wrapper()
            w_mod.attach_method(self.space, name, W_BuiltinFunction(name, func))
        yield w_mod
