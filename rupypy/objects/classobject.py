from pypy.rlib import jit

from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_BaseObject, W_Object


class VersionTag(object):
    pass

class W_ClassObject(W_BaseObject):
    _immutable_fields_ = ["version?"]

    classdef = ClassDef("Class", W_BaseObject.classdef)

    def __init__(self, name, superclass, is_singleton=False):
        self.name = name
        self.superclass = superclass
        self.is_singleton = is_singleton
        self.version = VersionTag()
        self.methods = {}
        self.constants_w = {}

    def mutated(self):
        self.version = VersionTag()

    def add_method(self, space, name, method):
        self.mutated()
        self.methods[name] = method

    def find_method(self, space, method):
        res = self._find_method_pure(space, method, self.version)
        if res is None:
            if self.superclass is not None:
                return self.superclass.find_method(space, method)
        return res

    @jit.elidable
    def _find_method_pure(self, space, method, version):
        return self.methods.get(method, None)

    def set_const(self, space, name, w_obj):
        self.mutated()
        self.constants_w[name] = w_obj

    def find_const(self, space, name):
        return self._find_const_pure(name, self.version)

    @jit.elidable
    def _find_const_pure(self, name, version):
        return self.constants_w.get(name, None)


    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr(self.name)

    @classdef.method("new")
    def method_new(self, space, args_w):
        w_obj = W_Object(space, self)
        space.send(w_obj, space.newsymbol("initialize"), args_w)
        return w_obj