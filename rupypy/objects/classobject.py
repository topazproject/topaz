from pypy.rlib import jit

from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object


class VersionTag(object):
    pass

class W_ClassObject(W_Object):
    _immutable_fields_ = ["version?"]

    classdef = ClassDef("Class", W_Object.classdef)

    def __init__(self, name, superclass):
        self.name = name
        self.superclass = superclass
        self.version = VersionTag()
        self.methods_w = {}

    def mutated(self):
        self.version = VersionTag()

    def add_method(self, name, method):
        self.mutated()
        self.methods_w[name] = method

    def find_method(self, space, method):
        res = self._find_method_pure(space, method, self.version)
        if res is None:
            if self.superclass is not None:
                return self.superclass.find_method(space, method)
            raise LookupError(method)
        return res

    @jit.elidable
    def _find_method_pure(self, space, method, version):
        return self.methods_w.get(method, None)


    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr([c for c in self.name])