from rupypy.module import ClassDef
from rupypy.modules.enumerable import Enumerable
from rupypy.objects.objectobject import W_Object


class W_RangeObject(W_Object):
    classdef = ClassDef("Range", W_Object.classdef)
    classdef.include_module(Enumerable)

    def __init__(self, space, w_start, w_end, exclusive):
        W_Object.__init__(self, space)
        self.w_start = w_start
        self.w_end = w_end
        self.exclusive = exclusive

    @classdef.singleton_method("new")
    def method_new(self, space, args_w):
        if len(args_w) < 3:
            return W_RangeObject(space, args_w[0], args_w[1], False)
        else:
            return W_RangeObject(space, args_w[0], args_w[1], space.bool_w(args_w[2]))

    @classdef.method("==")
    def method_eql(self, space, w_other):
        if isinstance(w_other, W_RangeObject):
            if space.int_w(self.w_start) == space.int_w(w_other.w_start):
                if space.int_w(self.w_end) == space.int_w(w_other.w_end):
                    if self.exclusive == w_other.exclusive:
                        return space.newbool(True)
        return space.newbool(False)

    @classdef.method("===")
    def method_eqleql(self, space, w_other):
        return self.include(w_other)

    classdef.app_method("""
    def member?(elem)
        include?
    end
    """)

    classdef.app_method("""
    def include?(elem)
        self.each do |i|
            return true if i == elem
        end
        false
    end
    """)

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
