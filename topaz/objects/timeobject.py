import time

from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object


class W_TimeObject(W_Object):
    classdef = ClassDef("Time", W_Object.classdef, filepath=__file__)

    def __init__(self, space, klass):
        W_Object.__init__(self, space, klass)
        self.epoch_seconds = 0

    @classdef.singleton_method("allocate")
    def method_allocate(self, space):
        return W_TimeObject(space, self)

    @classdef.singleton_method("now")
    def method_now(self, space):
        return space.send(self, space.newsymbol("new"))

    @classdef.method("initialize")
    def method_initialize(self, space):
        self.epoch_seconds = time.time()

    @classdef.method("to_f")
    def method_to_f(self, space):
        return space.newfloat(self.epoch_seconds)

    @classdef.method("-")
    def method_sub(self, space, w_other):
        assert isinstance(w_other, W_TimeObject)
        return space.newfloat(self.epoch_seconds - w_other.epoch_seconds)
