from topaz.module import ClassDef
from topaz.modules.enumerable import Enumerable
from topaz.objects.objectobject import W_Object


class W_RangeObject(W_Object):
    classdef = ClassDef("Range", W_Object.classdef)
    classdef.include_module(Enumerable)
    _immutable_fields_ = ["w_start", "w_end", "exclusive"]

    def __init__(self, space, w_start, w_end, exclusive):
        W_Object.__init__(self, space)
        self.w_start = w_start
        self.w_end = w_end
        self.exclusive = exclusive

    @classdef.singleton_method("allocate")
    def method_allocate(self, space):
        return W_RangeObject(space, None, None, False)

    @classdef.method("initialize", excl="bool")
    def method_initialize(self, space, w_start, w_end, excl=False):
        if self.w_start is not None or self.w_end is not None:
            raise space.error(space.w_NameError, "`initialize' called twice")
        if space.send(w_start, "<=>", [w_end]) is space.w_nil:
            raise space.error(space.w_ArgumentError, "bad value for range")

        self.w_start = w_start
        self.w_end = w_end
        self.exclusive = excl

    @classdef.method("begin")
    def method_begin(self, space):
        return self.w_start

    @classdef.method("end")
    def method_end(self, space):
        return self.w_end

    @classdef.method("exclude_end?")
    def method_exclude_end(self, space):
        return space.newbool(self.exclusive)
