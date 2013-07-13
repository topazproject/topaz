import time

from topaz.module import ClassDef
from topaz.coerce import Coerce
from topaz.objects.objectobject import W_Object


class W_TimeObject(W_Object):
    classdef = ClassDef("Time", W_Object.classdef)

    def __init__(self, space, klass):
        W_Object.__init__(self, space, klass)
        self._set_epoch_seconds(0.0)

    @classdef.singleton_method("allocate")
    def method_allocate(self, space):
        return W_TimeObject(space, self)

    @classdef.singleton_method("now")
    def method_now(self, space):
        return space.send(self, "new")

    @classdef.singleton_method("at")
    def method_at(self, space, w_time):
        if not (w_time.is_kind_of(space, space.w_numeric) or
                w_time.is_kind_of(space, space.getclassfor(W_TimeObject))):
            raise space.error(space.w_TypeError)
        timestamp = Coerce.float(space, w_time)
        w_time = space.send(self, "new")
        w_time._set_epoch_seconds(timestamp)
        return w_time

    @classdef.method("initialize")
    def method_initialize(self, space):
        self._set_epoch_seconds(time.time())

    @classdef.method("to_f")
    def method_to_f(self, space):
        return space.newfloat(self.epoch_seconds)

    @classdef.method("-")
    def method_sub(self, space, w_other):
        assert isinstance(w_other, W_TimeObject)
        return space.newfloat(self.epoch_seconds - w_other.epoch_seconds)

    def _set_epoch_seconds(self, timestamp):
        self.epoch_seconds = timestamp
