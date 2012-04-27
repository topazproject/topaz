from pypy.rlib.rrandom import Random

from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_BaseObject


class W_Random(W_BaseObject):
    classdef = ClassDef("Random", W_BaseObject.classdef)

    def __init__(self):
        self.random = Random()

    @classdef.singleton_method("allocate")
    def method_allocate(self, space):
        return W_Random()

    @classdef.method("rand")
    def method_rand(self, space):
        return space.newfloat(self.random.random())
