from rupypy.module import ClassDef
from rupypy.modules.enumerable import Enumerable
from rupypy.objects.objectobject import W_Object, W_BuiltinObject


class W_RangeObject(W_BuiltinObject):
    classdef = ClassDef("Range", W_Object.classdef)
    classdef.include_module(Enumerable)

    def __init__(self, space, w_start, w_end, inclusive):
        W_BuiltinObject.__init__(self, space)
        self.w_start = w_start
        self.w_end = w_end
        self.inclusive = inclusive

    @classdef.method("begin")
    def method_begin(self, space):
        return self.w_start

    @classdef.method("end")
    def method_end(self, space):
        return self.w_end

    classdef.app_method("""
    def each
        i = self.begin
        yield i
        i += 1
        while i < self.end
            yield i
            i += 1
        end
    end
    """)
