from rupypy.module import ClassDef
from rupypy.modules.enumerable import Enumerable
from rupypy.objects.objectobject import W_BaseObject
from rupypy.objects.intobject import W_IntObject


class W_RangeObject(W_BaseObject):
    classdef = ClassDef("Range", W_BaseObject.classdef)
    classdef.include_module(Enumerable)

    def __init__(self, w_start, w_end, exclusive):
        self.w_start = w_start
        self.w_end = w_end
        self.exclusive = exclusive

    @classdef.method("begin")
    def method_begin(self, space):
        return self.w_start

    @classdef.method("end")
    def method_end(self, space):
        return self.w_end

    @classdef.method("exclude_end?")
    def method_exclude_end(self, space):
        return space.newbool(self.exclusive)

    @classdef.method("cover?")
    def method_cover(self, space, w_elem):
        start = space.int_w(self.w_start)
        end = space.int_w(self.w_end)
        elem = space.int_w(w_elem)
        if start <= elem:
            if self.exclusive:
                if elem < end:
                    return space.newbool(True)
            else:
                if elem <= end:
                    return space.newbool(True)
        return space.newbool(False)

    classdef.app_method("""
    def each
        i = self.begin
        lim = self.end
        if !self.exclude_end?
            lim = lim.succ
        end
        while i < lim
            yield i
            i = i.succ
        end
    end
    """)

    classdef.app_method("""
    def to_a
        x = []
        self.each do |elem|
            x << elem
        end
        x
    end
    """)
