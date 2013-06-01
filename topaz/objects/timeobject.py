import math
import time

from topaz.coerce import Coerce
from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object


class W_TimeObject(W_Object):
    classdef = ClassDef("Time", W_Object.classdef)

    def __init__(self, space, klass, epoch_seconds = 0, microseconds = 0, tzoffset = time.timezone):
        W_Object.__init__(self, space, klass)
        self.epoch_seconds = epoch_seconds
        self.microseconds = microseconds
        self.offset = tzoffset

    @classdef.singleton_method("allocate")
    def method_allocate(self, space):
        return W_TimeObject(space, self)

    @classdef.singleton_method("now")
    def method_now(self, space):
        return space.send(self, "new")

    @classdef.method("initialize")
    def method_initialize(self, space):
        self.epoch_seconds = time.time()

    @classmethod
    def num_exact(class_, space, w_obj):
        t = space.getclass(w_obj)
        if t.name == 'NilClass':
            raise space.error(space.w_TypeError,
                    "can't convert nil into an exact number")
        elif t in [space.w_fixnum, space.w_bignum, space.w_float]:
            return w_obj
        elif t in [space.w_string]:
            raise space.error(space.w_TypeError,
                    "can't convert %s into an exact number" % space.getclass(w_obj).name)
        else:
            if not space.respond_to(w_obj, "to_r"):
                if space.respond_to(w_obj, "to_int"):
                    raise space.error(space.w_TypeError,
                        "can't convert %s into an exact number" % space.getclass(w_obj).name)
            else:
                # FIXME other magic is required to support Rational
                raise space.error(space.w_TypeError,
                    "can't convert %s into an exact number" % space.getclass(w_obj).name)


    @classdef.singleton_method("at")
    def method_at(self, space, w_other, w_extra=None):
        if isinstance(w_other, W_TimeObject):
            return W_TimeObject(space, None, w_other.epoch_seconds)
        w_other = W_TimeObject.num_exact(space, w_other)
        if w_extra is None:
            w_extra = space.newfloat(0)
        else:
            w_extra = W_TimeObject.num_exact(space, w_extra)
        return W_TimeObject(space, None, 
                Coerce.float(space, space.send(w_other, "to_f")),
                Coerce.float(space, space.send(w_extra, "to_f")))

    @classdef.method("strftime")
    def method_strftime(self, space, w_obj):
        return space.newstr_fromstr(time.strftime(space.str_w(w_obj),
            time.gmtime(self.epoch_seconds)))

    @classdef.method("inspect")
    @classdef.method("to_s")
    def method_inspect(self, space):
        if self.offset == 0:
            return space.send(self, "strftime", 
                [space.newstr_fromstr("%Y-%m-%d %H:%M:%S UTC")])
        else:
            return space.send(self, "strftime", 
                [space.newstr_fromstr("%Y-%m-%d %H:%M:%S %Z")])

    @classdef.method("to_f")
    def method_to_f(self, space):
        return space.newfloat(self.epoch_seconds)

    @classdef.method("usec")
    def method_usec(self, space):
        usec = int(math.floor(math.modf(self.epoch_seconds)[0] * 100000))
        return space.newint(usec)

    @classdef.method("utc?")
    @classdef.method("gmt?")
    def method_utcp(self, space):
        return space.newbool(self.offset == 0)

    @classdef.method("-")
    def method_sub(self, space, w_other):
        assert isinstance(w_other, W_TimeObject)
        return space.newfloat(self.epoch_seconds - w_other.epoch_seconds)

    @classdef.method("+")
    def method_plus(self, space, w_other):
        if isinstance(w_other, W_TimeObject):
            raise space.error(space.w_TypeError, "time + time?")
        return W_TimeObject(space, None, self.epoch_seconds +
                Coerce.float(space, self.num_exact(space, w_other)))
