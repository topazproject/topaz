from pypy.rlib import jit

from rupypy.module import ClassDef
from rupypy.objects.moduleobject import W_ModuleObject
from rupypy.objects.objectobject import W_Object


class W_ClassObject(W_ModuleObject):
    classdef = ClassDef("Class", W_ModuleObject.classdef)

    def __init__(self, space, name, superclass, is_singleton=False):
        W_ModuleObject.__init__(self, space, name)
        self.superclass = superclass
        self.is_singleton = is_singleton
        self.constants_w = {}
        self._lazy_constants_w = None

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

    def getsingletonclass(self, space):
        if self.klass is None:
            self.klass = space.newclass(
                self.name, space.getclassfor(W_ClassObject), is_singleton=True
            )
        return self.klass

    def find_method(self, space, method):
        res = W_ModuleObject.find_method(self, space, method)
        if res is None and self.superclass is not None:
            res = self.superclass.find_method(space, method)
        return res

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

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr(self.name)

    @classdef.method("new")
    def method_new(self, ec, args_w):
        w_obj = ec.space.send(ec, self, ec.space.newsymbol("allocate"), args_w)
        ec.space.send(ec, w_obj, ec.space.newsymbol("initialize"), args_w)
        return w_obj

    @classdef.method("allocate")
    def method_allocate(self, space, args_w):
        return W_Object(space, self)
