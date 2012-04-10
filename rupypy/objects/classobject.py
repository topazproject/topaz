from pypy.rlib import jit

from rupypy.objects.objectobject import W_Object


class VersionTag(object):
    pass

class W_ClassObject(W_Object):
    _immutable_fields_ = ["version?"]

    def __init__(self, name):
        self.version = VersionTag()
        self.name = name
        self.methods_w = {}

    def mutated(self):
        self.version = VersionTag()

    def add_method(self, name, method):
        self.mutated()
        self.methods_w[name] = method

    def find_method(self, space, method):
        return self._find_method_pure(space, method, self.version)

    @jit.elidable
    def _find_method_pure(self, space, method, version):
        return self.methods_w[method]