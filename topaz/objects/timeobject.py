import os

from topaz.utils import time
from topaz.coerce import Coerce
from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object


class W_TimeObject(W_Object):
    classdef = ClassDef("Time", W_Object.classdef, filepath=__file__)

    def __init__(self, space, klass):
        W_Object.__init__(self, space, klass)
        self.epoch_seconds = 0.0
        self.struct_time = (0, 0, 0, 0, 0, 0, 0, 0, 0)

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

    @classdef.singleton_method("local", arg0="int")
    @classdef.singleton_method("mktime", arg0="int")
    def method_local(self, space, arg0, w_arg1=None, w_arg2=None, w_arg3=None,
                     w_arg4=None, w_arg5=None, w_arg6=None, w_arg7=None,
                     w_arg8=None, w_arg9=None, w_arg10=None):
        args_raw_w = [
            w_arg1, w_arg2, w_arg3, w_arg4, w_arg5, w_arg6, w_arg7, w_arg8,
            w_arg9, w_arg10
        ]
        args_w = [
            w_arg if w_arg is not None and w_arg is not space.w_nil
                else space.newint(0) for w_arg in args_raw_w
        ]
        args_filtered_w = []
        for w_arg in [space.newint(0)] + args_raw_w:
            if w_arg is not None and w_arg is not space.w_nil:
                args_filtered_w.append(w_arg)

        n_args = len(args_filtered_w)
        if n_args == 9:
            raise space.error(space.w_ArgumentError, "%s for 1..8" % n_args)
        if n_args == 11:
            raise space.error(space.w_ArgumentError, "%s for 1..10" % n_args)

        w_time = W_TimeObject(space, self)
        # this assumes signatures where "year" is first argument
        month, day, hour, minute, sec = [
            Coerce.int(space, w_arg) for w_arg in args_w[:5]
        ]
        w_time.struct_time = (
            arg0, month, day, hour, minute, sec, 0, 0, 0
        )
        w_time.epoch_seconds = time.mktime(space, w_time.struct_time)
        return w_time

    @classdef.method("initialize")
    def method_initialize(self, space):
        self.struct_time = self.get_time_struct(space)
        self.epoch_seconds = time.mktime(space, self.struct_time)

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
        return time.strftime(space, '%Y-%m-%d %H:%M:%S %z', self.struct_time)
