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
        if isinstance(w_sec, W_TimeObject):
            args = w_sec.time_struct[:5]
            epoch = w_sec.epoch % 60
        else:
            if w_usec:
                usec = space.float_w(w_usec) / 1000
            else:
                usec = 0.0
            sec = int(space.float_w(w_sec))
            args = time.localtime(sec)[:5]
            epoch = (sec + usec) % 60
        args_w = [space.newint(i) for i in args]
        args_w.append(space.newfloat(epoch))
        return space.send(space.getclassfor(W_TimeObject), space.newsymbol("new"), args_w)

    @classdef.method("initialize")
    def method_initialize(self, space, args_w):
        if not args_w:
            self.epoch = time.time()
            self.time_struct = time.localtime(self.epoch)
        else:
            if len(args_w) > 6:
                raise NotImplementedError("Time.new with utc_offset")
            args = [space.float_w(i) for i in args_w]
            args += [0] * (6 - len(args))
            struct = time.strptime(
                "%04d %02d %02d %02d %02d %02d" % tuple(args),
                "%Y %m %d %H %M %S"
            )
            self.time_struct = struct
            self.epoch = time.mktime(struct) + (args[5] % 1)

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr(time.strftime("%Y-%m-%d %H:%M:%S %z", self.time_struct))

    @classdef.method("to_f")
    def method_to_f(self, space):
        return space.newfloat(self.epoch)

    @classdef.method("-")
    def method_minus(self, space, w_other):
        assert isinstance(w_other, W_TimeObject)
        return space.send(
            space.getclassfor(W_TimeObject),
            space.newsymbol("at"),
            [space.newfloat(self.epoch - w_other.epoch)]
        )
