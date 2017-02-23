import math
import time

from topaz.module import ClassDef
from topaz.coerce import Coerce
from topaz.objects.objectobject import W_Object
from topaz.modules.comparable import Comparable


MONTHNAMES = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


class W_TimeObject(W_Object):
    classdef = ClassDef("Time", W_Object.classdef)
    classdef.include_module(Comparable)

    def __init__(self, space, klass):
        W_Object.__init__(self, space, klass)
        self._set_epoch_seconds(0.0)
        self._set_offset(0)

    @classdef.singleton_method("allocate")
    def method_allocate(self, space):
        return W_TimeObject(space, self)

    @classdef.singleton_method("now")
    def method_now(self, space):
        return space.send(self, "new")

    @classdef.singleton_method("new")
    def method_now(self, space, args_w):
        if len(args_w) > 7:
            raise space.error(
                space.w_ArgumentError,
                "wrong number of arguments (given %d, expected 0..7)" % len(args_w)
            )
        if len(args_w) > 6:
            utc_offset = Coerce.int(space, args_w.pop())
            w_time = space.send(self, "gm", args_w)
            w_time._set_offset(utc_offset)
            return w_time
        elif len(args_w) > 1:
            return space.send(self, "gm", args_w)
        else:
            w_time = space.send(self, "allocate")
            space.send(w_time, "initialize")
            return w_time

    @classdef.singleton_method("at")
    def method_at(self, space, w_time, w_microtime=None):
        if not (w_time.is_kind_of(space, space.w_numeric) or
                w_time.is_kind_of(space, space.getclassfor(W_TimeObject))):
            raise space.error(space.w_TypeError)
        if w_microtime is not None:
            microtime = Coerce.float(space, w_microtime) * 0.000001
        else:
            microtime = 0.0
        timestamp = Coerce.float(space, w_time)
        w_time = space.send(self, "new")
        w_time._set_epoch_seconds(timestamp + microtime)
        return w_time

    @classdef.singleton_method("gm")
    def method_gm(self, space, args_w):
        if len(args_w) == 0:
            raise space.error(
                space.w_ArgumentError,
                "wrong number of arguments (given 0, expected 1..8)"
            )
        elif len(args_w) == 10:
            # sec, min, hour, day, month, year, dummy, dummy, dummy, dummy
            sec = Coerce.int(space, args_w[0])
            minute = Coerce.int(space, args_w[1])
            hour = Coerce.int(space, args_w[2])
            day = Coerce.int(space, args_w[3])
            month = W_TimeObject.month_arg_to_month(space, args_w[4])
            year = Coerce.int(space, args_w[5])
            usecfrac = 0.0
        else:
            month = day = 1
            hour = minute = sec = 0
            usecfrac = 0.0
            year = Coerce.int(space, args_w[0])
            if len(args_w) > 1:
                month = W_TimeObject.month_arg_to_month(space, args_w[1])
            if len(args_w) > 2:
                day = Coerce.int(space, args_w[2])
            if len(args_w) > 3:
                hour = Coerce.int(space, args_w[3])
            if len(args_w) > 4:
                minute = Coerce.int(space, args_w[4])
            if len(args_w) > 6:
                sec = Coerce.int(space, args_w[5])
                usecfrac = Coerce.float(space, args_w[6]) / 1000000
            if len(args_w) > 5:
                fsec = Coerce.float(space, args_w[5])
                sec = int(math.floor(fsec))
                usecfrac = fsec - sec

        if not (1 <= month < 12):
            raise space.error(space.w_ArgumentError, "mon out of range")
        if not (1 <= day < 31):
            raise space.error(space.w_ArgumentError, "argument out of range")
        if not (0 <= hour < 24):
            raise space.error(space.w_ArgumentError, "argument out of range")
        if not (0 <= minute < 60):
            raise space.error(space.w_ArgumentError, "argument out of range")
        if not (0 <= sec < 60):
            raise space.error(space.w_ArgumentError, "argument out of range")

        w_time = space.send(space.getclassfor(W_TimeObject), "new")
        w_time._set_epoch_seconds(mktime(year, month, day, hour, minute, sec) + usecfrac)
        return w_time

    @staticmethod
    def month_arg_to_month(space, w_arg):
        w_month = space.convert_type(w_arg, space.w_string, "to_str", raise_error=False)
        if w_month is space.w_nil:
            month = Coerce.int(space, w_arg)
        else:
            try:
                month = MONTHNAMES.index(space.str_w(w_month)) + 1
            except ValueError:
                raise space.error(
                    space.w_ArgumentError,
                    "mon out of range"
                )
        return month

    @classdef.method("initialize")
    def method_initialize(self, space):
        self._set_epoch_seconds(time.time())
        self._set_offset(time.timezone)

    @classdef.method("to_f")
    def method_to_f(self, space):
        return space.newfloat(self.epoch_seconds)

    @classdef.method("to_i")
    def method_to_i(self, space):
        return space.newint(int(self.epoch_seconds))

    @classdef.method("+")
    def method_plus(self, space, w_other):
        if isinstance(w_other, W_TimeObject):
            raise space.error(space.w_TypeError, "time + time?")
        w_time = space.send(space.getclassfor(W_TimeObject), "allocate")
        w_time._set_epoch_seconds(self.epoch_seconds + Coerce.float(space, w_other))
        w_time._set_offset(self.offset)
        return w_time

    @classdef.method("-")
    def method_sub(self, space, w_other):
        if isinstance(w_other, W_TimeObject):
            return space.newfloat(self.epoch_seconds - Coerce.float(space, w_other))
        else:
            w_time = space.send(space.getclassfor(W_TimeObject), "allocate")
            w_time._set_epoch_seconds(self.epoch_seconds - Coerce.float(space, w_other))
            w_time._set_offset(self.offset)
            return w_time

    @classdef.method("strftime")
    def method_strftime(self, space, w_obj):
        return space.newstr_fromstr(strftime(space.str_w(w_obj),
                                             self.epoch_seconds))

    @classdef.method("gmtime")
    @classdef.method("inspect")
    @classdef.method("to_s")
    def method_inspect(self, space):
        if self.offset == 0:
            return space.send(self, "strftime",
                              [space.newstr_fromstr("%Y-%m-%d %H:%M:%S UTC")])
        else:
            return space.send(self, "strftime",
                              [space.newstr_fromstr("%Y-%m-%d %H:%M:%S %Z")])

    @classdef.method("usec")
    def method_usec(self, space):
        usec = int(math.floor(math.modf(self.epoch_seconds)[0] * 100000))
        return space.newint(usec)

    @classdef.method("to_a")
    def method_to_a(self, space):
        tp = gmtime(int(self.epoch_seconds))
        tp_w = [space.newint(f) for f in tp]
        if self.offset == 0:
            tp_w.append(space.newstr_fromstr("UTC"))
        else:
            tp_w.append(space.newstr_fromstr(strftime("%Z", self.epoch_seconds)))
        return space.newarray(tp_w)

    @classdef.method("utc?")
    @classdef.method("gmt?")
    def method_utcp(self, space):
        return space.newbool(self.offset == 0)

    def _set_epoch_seconds(self, timestamp):
        self.epoch_seconds = timestamp

    def _set_offset(self, tzoffset):
        self.offset = tzoffset


from rpython.rtyper.lltypesystem import lltype, rffi
from rpython.rlib.rarithmetic import intmask
from pypy.module.time.interp_time import external, TM_P, glob_buf

c_gmtime = external('gmtime', [rffi.TIME_TP], TM_P, save_err=rffi.RFFI_SAVE_ERRNO)
c_strftime = external('strftime', [rffi.CCHARP, rffi.SIZE_T, rffi.CCHARP, TM_P], rffi.SIZE_T)
c_mktime = external('mktime', [TM_P], rffi.TIME_T)

def strftime(format, seconds):
    i = 1024
    while i < (256 * len(format)):
        # if the buffer is 256 times as long as the format, we're not failing
        # for lack of room (see pypy)
        with lltype.scoped_alloc(rffi.TIME_TP.TO, 1) as t_ref:
            t_ref[0] = int(seconds)
            p = c_gmtime(t_ref)
            with lltype.scoped_alloc(rffi.CCHARP.TO, i) as outbuf:
                buflen = c_strftime(outbuf, i, format, p)
                if buflen > 0:
                    return rffi.charp2strn(outbuf, intmask(buflen))
        i += i
    return ""


def gmtime(seconds):
    with lltype.scoped_alloc(rffi.TIME_TP.TO, 1) as t_ref:
        t_ref[0] = seconds
        t = c_gmtime(t_ref)
        return [
            rffi.getintfield(t, 'c_tm_sec'),
            rffi.getintfield(t, 'c_tm_min'),
            rffi.getintfield(t, 'c_tm_hour'),
            rffi.getintfield(t, 'c_tm_mday'),
            rffi.getintfield(t, 'c_tm_mon') + 1, # want january == 1
            rffi.getintfield(t, 'c_tm_year') + 1900,
            (rffi.getintfield(t, 'c_tm_wday') + 6) % 7, # want monday == 0
            rffi.getintfield(t, 'c_tm_yday') + 1, # want january, 1 == 1
            rffi.getintfield(t, 'c_tm_isdst')]


def mktime(year, month, day, hour, minute, second):
    rffi.setintfield(glob_buf, 'c_tm_year', year - 1900)
    rffi.setintfield(glob_buf, 'c_tm_mon', month - 1)
    rffi.setintfield(glob_buf, 'c_tm_mday', day)
    rffi.setintfield(glob_buf, 'c_tm_hour', hour)
    rffi.setintfield(glob_buf, 'c_tm_min', minute)
    rffi.setintfield(glob_buf, 'c_tm_sec', second)
    rffi.setintfield(glob_buf, 'c_tm_wday', -1)
    tt = c_mktime(glob_buf)
    return float(tt)
