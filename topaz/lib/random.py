from rpython.rlib.rrandom import Random

from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object


class W_RandomObject(W_Object):
    classdef = ClassDef("Random", W_Object.classdef, filepath=__file__)

    def __init__(self, space, klass=None):
        W_Object.__init__(self, space, klass)
        self.random = Random()

    @classdef.singleton_method("allocate")
    def method_allocate(self, space):
        return W_RandomObject(space, self)

    @classdef.method("rand")
    def method_rand(self, space):
        return space.newfloat(self.random.random())
