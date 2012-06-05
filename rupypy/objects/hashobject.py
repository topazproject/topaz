from rupypy.module import ClassDef
from rupypy.modules.enumerable import Enumerable
from rupypy.objects.objectobject import W_BaseObject
from rupypy.objects.rangeobject import W_RangeObject

class W_HashObject(W_BaseObject):
    classdef = ClassDef("Hash", W_BaseObject.classdef)
    classdef.include_module(Enumerable)

    def __init__(self, dict_w = None):
        if dict_w is None:
            self.dict_w = dict()
        else:
            self.dict_w = dict_w

    classdef.app_method("""
    def to_s()
        result = "{"
        i = 0
        self.each_with_index do |obj, i|
            if i > 0
                result << ", "
            end
            result << obj[0].to_s << " => " << obj[1].to_s
        end
        result << "}"
    end
    """)

    @classdef.method("[]")
    def method_at(self, space, w_key):
        return self.dict_w.get(w_key, space.w_nil)

    @classdef.method("[]=")
    def method_at_put(self, space, w_key, w_obj):
        self.dict_w[w_key] = w_obj
        return w_obj

    @classdef.method("size")
    @classdef.method("length")
    def method_length(self, space):
        return space.newint(len(self.dict_w))

    @classdef.method("keys")
    def method_keys(self, space):
        return space.newarray(self.dict_w.keys())

    @classdef.method("values")
    def method_values(self, space):
        return space.newarray(self.dict_w.values())

    @classdef.method("length")
    def method_length(self, space):
        return space.newint(len(self.dict_w))

    classdef.app_method("""
    def each
        i = 0
        k = self.keys
        while i < self.length
            yield *[k[i], self[k[i]]]
            i += 1
        end
    end
    """)
