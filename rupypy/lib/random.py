from pypy.rlib.rrandom import Random

from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object


class W_RandomObject(W_Object):
    classdef = ClassDef("Random", W_Object.classdef)

    def __init__(self, space, klass=None):
        W_Object.__init__(self, space, klass)
        self.random = Random()

    @classdef.singleton_method("allocate")
    def method_allocate(self, space):
        return W_RandomObject(space, self)

    @classdef.method("rand")
    def method_rand(self, space):
        return space.newfloat(self.random.random())
