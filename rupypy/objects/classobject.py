from pypy.rlib import jit

from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_BaseObject


class VersionTag(object):
    pass

class W_ClassObject(W_BaseObject):
    _immutable_fields_ = ["version?"]

    classdef = ClassDef("Class", W_BaseObject.classdef)

    def __init__(self, name, superclass):
        self.name = name
        self.superclass = superclass
        self.version = VersionTag()
        self.methods = {}

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


    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr(self.name)