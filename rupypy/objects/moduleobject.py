from pypy.rlib import jit

from rupypy.module import ClassDef
from rupypy.objects.functionobject import W_FunctionObject
from rupypy.objects.objectobject import W_BaseObject, W_Object

class AttributeReader(W_FunctionObject):
    _immutable_fields_ = ["varname"]

    def __init__(self, varname):
        self.varname = varname

    def call(self, space, w_obj, args_w, block):
        return space.find_instance_var(w_obj, self.varname)


class AttributeWriter(W_FunctionObject):
    _immutable_fields_ = ["varname"]

    def __init__(self, varname):
        self.varname = varname

    def call(self, space, w_obj, args_w, block):
        [w_value] = args_w
        space.set_instance_var(w_obj, self.varname, w_value)
        return w_value


class VersionTag(object):
    pass


class W_ModuleObject(W_Object):
    _immutable_fields_ = ["version?"]

    classdef = ClassDef("Module", W_Object.classdef)

    def __init__(self, space, name, superclass):
        W_Object.__init__(self, space, self)
        self.name = name
        self.superclass = superclass
        self.klass = None
        self.version = VersionTag()
        self.methods_w = {}
        self.constants_w = {}
        self._lazy_constants_w = None
        self.included_modules = []
        self.descendants = []

    def _freeze_(self):
        "NOT_RPYTHON"
        if self._lazy_constants_w is not None:
            for name in self._lazy_constants_w.keys():
                self._load_lazy(name)
            self._lazy_constants_w = None
        return False

    def _lazy_set_const(self, space, name, obj):
        "NOT_RPYTHON"
        if self._lazy_constants_w is None:
            self._lazy_constants_w = {}
        self._lazy_constants_w[name] = (space, obj)

    def _load_lazy(self, name):
        "NOT_RPYTHON"
        obj = self._lazy_constants_w.pop(name, None)
        if obj is not None:
            space, obj = obj
            if hasattr(obj, "classdef"):
                self.set_const(self, obj.classdef.name, space.getclassfor(obj))
            elif hasattr(obj, "moduledef"):
                self.set_const(self, obj.moduledef.name, space.getmoduleobject(obj.moduledef))
            else:
                assert False

    def mutated(self):
        self.version = VersionTag()

    def define_method(self, space, name, method):
        self.mutated()
        self.methods_w[name] = method

    def find_method(self, space, name):
        method = self._find_method_pure(space, name, self.version)
        if method is None:
            if len(self.included_modules) > 0:
                for module in self.included_modules:
                    method = module.find_method(space, name)
                    if method is not None:
                        return method
            return None
        else:
            return method

    @jit.elidable
    def _find_method_pure(self, space, method, version):
        return self.methods_w.get(method, None)

    def set_const(self, space, name, w_obj):
        self.mutated()
        self.constants_w[name] = w_obj

    def find_const(self, space, name):
        res = self._find_const_pure(name, self.version)
        if res is None and self.superclass is not None:
            res = self.superclass.find_const(space, name)
        return res

    @jit.elidable
    def _find_const_pure(self, name, version):
        if self._lazy_constants_w is not None:
            self._load_lazy(name)
        return self.constants_w.get(name, None)

    def getclass(self, space):
        if self.klass is not None:
            return self.klass
        return W_BaseObject.getclass(self, space)

    def getsingletonclass(self, space):
        if self.klass is None:
            self.mutated()
            self.klass = space.newclass(
                self.name, space.getclassfor(W_ModuleObject), is_singleton=True
            )
        return self.klass

    def ancestors(self):
        return [self] + self.included_modules

    def include_module(self, space, w_mod):
        if w_mod not in self.ancestors():
            self.included_modules.insert(0, w_mod)
            w_mod.included(space, self)

    def included(self, space, w_mod):
        self.descendants.append(w_mod)
        space.send(self, space.newsymbol("included"), [w_mod])

    def inherited(self, space, w_mod):
        self.descendants.append(w_mod)
    def set_visibility(self, space, names_w, visibility):
        names = [space.symbol_w(w_name) for w_name in names_w]
        if names:
            for name in names:
                self.set_method_visibility(space, name, visibility)
        else:
            self.set_default_visibility(space, visibility)

    def set_default_visibility(self, space, visibility):
        pass

    def set_method_visibility(self, space, name, visibility):
        pass

    @classdef.method("include")
    def method_include(self, space, w_mod):
        assert isinstance(w_mod, W_ModuleObject)
        space.send(w_mod, space.newsymbol("append_features"), [self])

    @classdef.method("append_features")
    def method_append_features(self, space, w_mod):
        ancestors = self.ancestors()
        for idx in xrange(len(ancestors) - 1, -1, -1):
            w_mod.include_module(space, ancestors[idx])

    @classdef.method("attr_accessor")
    def method_attr_accessor(self, space, args_w):
        for w_arg in args_w:
            varname = space.symbol_w(w_arg)
            self.method_attr_reader(space, varname)
            self.define_method(space, varname + "=", AttributeWriter("@" + varname))

    @classdef.method("attr_reader", varname="symbol")
    def method_attr_reader(self, space, varname):
        self.define_method(space, varname, AttributeReader("@" + varname))

    @classdef.method("module_function", name="symbol")
    def method_module_function(self, space, name):
        self.attach_method(space, name, self.find_method(space, name))

    @classdef.method("private_class_method")
    def method_private_class_method(self, space, w_name):
        w_cls = self.getsingletonclass(space)
        return space.send(w_cls, space.newsymbol("private"), [w_name])

    @classdef.method("public_class_method")
    def method_public_class_method(self, space, w_name):
        w_cls = self.getsingletonclass(space)
        return space.send(w_cls, space.newsymbol("public"), [w_name])

    @classdef.method("alias_method", new_name="symbol", old_name="symbol")
    def method_alias_method(self, space, new_name, old_name):
        self.define_method(space, new_name, self.find_method(space, old_name))

    @classdef.method("ancestors")
    def method_ancestors(self, space):
        return space.newarray(self.ancestors())

    @classdef.method("included")
    def method_included(self, space, w_mod):
        pass

    @classdef.method("name")
    def method_name(self, space):
        return space.newstr_fromstr(self.name)

    @classdef.method("private")
    def method_private(self, space, args_w):
        self.set_visibility(space, args_w, "private")

    @classdef.method("public")
    def method_public(self, space, args_w):
        self.set_visibility(space, args_w, "public")

    @classdef.method("protected")
    def method_protected(self, space, args_w):
        self.set_visibility(space, args_w, "protected")
