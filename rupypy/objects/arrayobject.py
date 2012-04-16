from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_BaseObject


class W_ArrayObject(W_BaseObject):
    classdef = ClassDef("Array", W_BaseObject.classdef)

    def __init__(self, items_w):
        self.items_w = items_w

    classdef.app_method("""
    def to_s()
        result = "["
        i = 0
        while i < self.length
            if i > 0
                result << ", "
            end
            result << self[i].to_s
            i = i + 1
        end
        result << "]"
    end
    """)

    @classdef.method("[]", idx=int)
    def method_subscript(self, space, idx):
        return self.items_w[idx]

    @classdef.method("length")
    def method_length(self, space):
        return space.newint(len(self.items_w))

    @classdef.method("<<")
    def method_lshift(self, space, w_obj):
        self.items_w.append(w_obj)
        return self

    classdef.app_method("""
    def each
        i = 0
        while i < self.length
            yield self[i]
            i = i + 1
        end
    end
    """)