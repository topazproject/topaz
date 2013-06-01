import os

from topaz.utils import time
from topaz.coerce import Coerce
from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object


class W_TimeObject(W_Object):
    classdef = ClassDef("Time", W_Object.classdef)

    def __init__(self, space, klass):
        W_Object.__init__(self, space, klass)
        self.epoch_seconds = 0.0
        self.struct_time = (1970, 1, 1, 0, 0, 0, 0, 0, 0)

    def get_time_struct(self, space, w_secs=None):
        return time.localtime(space, w_secs)

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        time._init_accept2dyear(space)
        time._init_timezone(space)

    @classdef.singleton_method("allocate")
    def method_allocate(self, space):
        return W_TimeObject(space, self)

    @classdef.singleton_method("now")
    def method_now(self, space):
        return space.send(self, "new")

    @classdef.singleton_method("local", year_or_sec="int")
    @classdef.singleton_method("mktime", year_or_sec="int")
    def method_local(self, space, year_or_sec, w_month_or_min=None,
                     w_day_or_hour=None, w_hour_or_day=None,
                     w_min_or_month=None, w_sec_or_year=None,
                     w_usec_with_frac_or_wday=None, w_yday=None,
                     w_isdst=None, w_tz=None, w_unknown=None):
        args_raw_w = [
            w_month_or_min, w_day_or_hour, w_hour_or_day, w_min_or_month,
            w_sec_or_year, w_usec_with_frac_or_wday, w_yday, w_isdst, w_tz,
            w_unknown
        ]
        args_w = [
            w_arg if w_arg is not None and w_arg is not space.w_nil
                else space.newint(0) for w_arg in args_raw_w
        ]
        n_args = 0
        for w_arg in [space.newint(0)] + args_raw_w:
            if w_arg is not None and w_arg is not space.w_nil:
                n_args += 1

        if n_args == 9:
            raise space.error(space.w_ArgumentError, "%s for 1..8" % n_args)
        if n_args == 11:
            raise space.error(space.w_ArgumentError, "%s for 1..10" % n_args)
        if n_args > 6:
            raise space.error(space.w_NotImplementedError)

        w_time = W_TimeObject(space, self)
        # FIXME the following assumes signatures where "year" is first argument
        month, day, hour, minute, sec = [
            Coerce.int(space, w_arg) for w_arg in args_w[:5]
        ]
        w_time.struct_time = (
            year_or_sec,                # tm_year
            1 if month == 0 else month, # tm_mon
            1 if day == 0 else day,     # tm_mday
            hour,                       # tm_hour
            minute,                     # tm_min
            sec,                        # tm_sec
            0,                          # tm_wday
            0,                          # tm_yday
            0                           # tm_isdst
        )
        w_time.epoch_seconds = time.mktime(space, w_time.struct_time)
        return w_time

    @classdef.method("initialize")
    def method_initialize(self, space):
        self.epoch_seconds = time.time()
        self.struct_time = self.get_time_struct(space, space.newfloat(self.epoch_seconds))

    @classdef.method("asctime")
    def method_asctime(self, space):
        return space.newstr_fromstr(time.asctime(space, self.struct_time))

    @classdef.method("ctime")
    def method_ctime(self, space):
        return space.newstr_fromstr(
            time.ctime(space, space.newfloat(self.epoch_seconds))
        )

    @classdef.method("strftime", fmt="str")
    def method_strftime(self, space, fmt):
        return space.newstr_fromstr(time.strftime(space, fmt, self.struct_time))

    @classdef.method("to_f")
    def method_to_f(self, space):
        return space.newfloat(self.epoch_seconds)

    @classdef.method("-")
    def method_sub(self, space, w_other):
        assert isinstance(w_other, W_TimeObject)
        return space.newfloat(self.epoch_seconds - w_other.epoch_seconds)

    @classdef.method("==")
    def method_equals(self, space, w_other):
        assert isinstance(w_other, W_TimeObject)
        return space.newbool(self.struct_time == w_other.struct_time)

    @classdef.method("to_s")
    @classdef.method("inspect")
    def method_to_s(self, space):
        return space.newstr_fromstr(
            time.strftime(space, '%Y-%m-%d %H:%M:%S %z', self.struct_time)
        )

    @classdef.method("to_i")
    def method_to_i(self, space):
        return space.newint(int(self.epoch_seconds))
