import functools

from topaz.gateway import WrapperGenerator
from topaz.utils.cache import Cache


class ClassDef(object):
    def __init__(self, name, superclassdef=None):
        self.name = name
        self.methods = {}
        self.singleton_methods = {}
        self.includes = []
        self.setup_class_func = None
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

    def singleton_method(self, __name, **argspec):
        name = __name

        def adder(func):
            if isinstance(func, staticmethod):
                func = func.__func__
            self.singleton_methods[name] = (func, argspec)
            return staticmethod(func)
        return adder

    def setup_class(self, func):
        self.setup_class_func = func
        return func

    def undefine_allocator(self):
        @self.singleton_method("allocate")
        def method_allocate(self, space):
            raise space.error(
                space.w_TypeError, "allocator undefined for %s" % self.name)
        return method_allocate

    def notimplemented(self, name):
        @self.method(name)
        def method(self, space):
            raise space.error(space.w_NotImplementedError)

    def singleton_notimplemented(self, name):
        @self.singleton_method(name)
        def method(self, space):
            raise space.error(space.w_NotImplementedError)


class ModuleDef(object):
    def __init__(self, name):
        self.name = name
        self.methods = {}

        self.singleton_methods = {}
        self.setup_module_func = None

    def __deepcopy__(self, memo):
        return self

    def method(self, __name, **argspec):
        name = __name

        def adder(func):
            self.methods[name] = (func, argspec)
            return func
        return adder

    def function(self, __name, **argspec):
        name = __name

        def adder(func):
            # TODO: should be private, once we have visibility
            self.methods[name] = (func, argspec)
            self.singleton_methods[name] = (func, argspec)
            return func
        return adder

    def setup_module(self, func):
        self.setup_module_func = func
        return func


def check_frozen(param="self"):
    def inner(func):
        code = func.__code__
        space_idx = code.co_varnames.index("space")
        obj_idx = code.co_varnames.index(param)

        @functools.wraps(func)
        def wrapper(*args):
            space = args[space_idx]
            w_obj = args[obj_idx]
            if space.is_true(w_obj.get_flag(space, "frozen?")):
                klass = space.getclass(w_obj)
                raise space.error(
                    space.w_RuntimeError,
                    "can't modify frozen %s" % klass.name)
            return func(*args)
        wrapper.__wraps__ = func
        return wrapper
    return inner


class ClassCache(Cache):
    def _build(self, classdef):
        from topaz.objects.classobject import W_ClassObject
        from topaz.objects.functionobject import W_BuiltinFunction

        assert classdef.cls is not None, classdef.name

        if classdef.superclassdef is None:
            superclass = None
        else:
            superclass = self.space.getclassobject(classdef.superclassdef)

        w_class = self.space.newclass(classdef.name, superclass)
        yield w_class
        for name, (method, argspec) in classdef.methods.iteritems():
            func = WrapperGenerator(
                name, method, argspec, classdef.cls).generate_wrapper()
            w_class.define_method(
                self.space, name, W_BuiltinFunction(name, w_class, func))

        for name, (method, argspec) in classdef.singleton_methods.iteritems():
            func = WrapperGenerator(
                name, method, argspec, W_ClassObject).generate_wrapper()
            w_class.attach_method(
                self.space, name, W_BuiltinFunction(name, w_class, func))

        for mod in reversed(classdef.includes):
            w_mod = self.space.getmoduleobject(mod.moduledef)
            self.space.send(w_class, "include", [w_mod])

        if classdef.setup_class_func is not None:
            classdef.setup_class_func(classdef.cls, self.space, w_class)


class ModuleCache(Cache):
    def _build(self, moduledef):
        from topaz.objects.functionobject import W_BuiltinFunction
        from topaz.objects.moduleobject import W_ModuleObject
        from topaz.objects.objectobject import W_BaseObject

        w_mod = self.space.newmodule(moduledef.name)
        for name, (method, argspec) in moduledef.methods.iteritems():
            func = WrapperGenerator(
                name, method, argspec, W_BaseObject).generate_wrapper()
            w_mod.define_method(
                self.space, name, W_BuiltinFunction(name, w_mod, func))
        for name, (method, argspec) in moduledef.singleton_methods.iteritems():
            func = WrapperGenerator(
                name, method, argspec, W_ModuleObject).generate_wrapper()
            w_mod.attach_method(
                self.space, name, W_BuiltinFunction(name, w_mod, func))

        if moduledef.setup_module_func is not None:
            moduledef.setup_module_func(self.space, w_mod)

        yield w_mod
