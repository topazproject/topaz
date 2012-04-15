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
