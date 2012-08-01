import time

from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object
from rupypy.objects.floatobject import W_FloatObject
from rupypy.objects.intobject import W_FixnumObject


class W_TimeObject(W_Object):
    classdef = ClassDef("Time", W_Object.classdef)

    @classdef.singleton_method("allocate")
    def method_allocate(self, space, args_w):
        return W_TimeObject(space)

    @classdef.singleton_method("now")
    def singleton_method_now(self, space):
        return space.send(space.getclassfor(W_TimeObject), space.newsymbol("new"))

    @classdef.singleton_method("at")
    def singleton_method(self, space, w_sec, w_usec=None):
        obj = space.send(space.getclassfor(W_TimeObject), space.newsymbol("new"))
        if isinstance(w_sec, W_TimeObject):
            obj.epoch = w_sec.epoch
        elif isinstance(w_sec, W_FixnumObject) or w_usec:
            if w_usec:
                usec = space.float_w(w_usec) / 1000
            else:
                usec = 0.0
            obj.epoch = int(space.float_w(w_sec)) + usec
        else:
            obj.epoch = space.float_w(w_sec)
        obj.time_struct = time.localtime(obj.epoch)
        return obj

    @classdef.method("initialize")
    def method_initialize(self, space, args_w):
        if not args_w:
            self.epoch = time.time()
            self.time_struct = time.localtime(self.epoch)
        else:
            raise NotImplementedError("Time.new(year, month, day, hour, min, sec, utc_offset)")

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr(time.strftime("%Y-%m-%d %H:%M:%S %z", self.time_struct))

    @classdef.method("to_f")
    def method_to_f(self, space):
        return space.newfloat(self.epoch)

    @classdef.method("-")
    def method_minux(self, space, w_other):
        assert isinstance(w_other, W_TimeObject)
        return space.send(
            space.getclassfor(W_TimeObject),
            space.newsymbol("at"),
            [space.newfloat(self.epoch - w_other.epoch)]
        )
