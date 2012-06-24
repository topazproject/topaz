from rupypy.module import ClassDef
from rupypy.modules.enumerable import Enumerable
from rupypy.objects.objectobject import W_Object
from rupypy.objects.rangeobject import W_RangeObject


class W_ArrayObject(W_Object):
    classdef = ClassDef("Array", W_Object.classdef)
    classdef.include_module(Enumerable)

    def __init__(self, space, items_w):
        W_Object.__init__(self, space)
        self.items_w = items_w

    def listview(self, space):
        return self.items_w

    classdef.app_method("""
    def to_s()
        result = "["
        i = 0
        self.each_with_index do |obj, i|
            if i > 0
                result << ", "
            end
            result << obj.to_s
        end
        result << "]"
    end
    """)

    @classdef.method("[]")
    def method_subscript(self, space, w_idx):
        if isinstance(w_idx, W_RangeObject):
            start = space.int_w(w_idx.w_start)
            if w_idx.exclusive:
                end = space.int_w(w_idx.w_end)
            else:
                end = space.int_w(w_idx.w_end) + 1
            return space.newarray(self.items_w[start:end])
        else:
            return self.items_w[space.int_w(w_idx)]

    @classdef.method("[]=")
    def method_subscript_assign(self, space, w_idx, w_obj):
        if isinstance(w_idx, W_RangeObject):
            start = space.int_w(w_idx.w_start)
            if w_idx.exclusive:
                end = space.int_w(w_idx.w_end)
            else:
                end = space.int_w(w_idx.w_end) + 1
            self.items_w[start:end] = [w_obj]
        else:
            self.items_w[space.int_w(w_idx)] = w_obj

    @classdef.method("size")
    @classdef.method("length")
    def method_length(self, space):
        return space.newint(len(self.items_w))

    @classdef.method("+")
    def method_add(self, space, w_other):
        assert isinstance(w_other, W_ArrayObject)
        return space.newarray(self.items_w + w_other.items_w)

    @classdef.method("<<")
    def method_lshift(self, space, w_obj):
        self.items_w.append(w_obj)
        return self

    @classdef.method("unshift")
    def method_unshift(self, space, args_w):
        for i in xrange(len(args_w) - 1, -1, -1):
            w_obj = args_w[i]
            self.items_w.insert(0, w_obj)
        return self

    classdef.app_method("""
    def at idx
        self[idx]
    end
    """)

    classdef.app_method("""
    def each
        i = 0
        while i < self.length
            yield self[i]
            i += 1
        end
    end
    """)

    classdef.app_method("""
    def zip ary
        result = []
        self.each_with_index do |obj, idx|
            result << [obj, ary[idx]]
        end
        result
    end
    """)

    classdef.app_method("""
    def product ary
        result = []
        self.each do |obj|
            ary.each do |other|
                result << [obj, other]
            end
        end
        result
    end
    """)
