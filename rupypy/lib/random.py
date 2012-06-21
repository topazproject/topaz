from pypy.rlib.rrandom import Random

from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object, W_BuiltinObject

class W_Random(W_BuiltinObject):
    classdef = ClassDef("Random", W_Object.classdef)

    def __init__(self, space):
        W_BuiltinObject.__init__(self, space)
        self.random = Random()

    @classdef.singleton_method("allocate")
    def method_allocate(self, space):
        return W_Random(space)

    @classdef.method("rand")
    def method_rand(self, space):
        return space.newfloat(self.random.random())
