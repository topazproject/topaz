from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_BaseObject


class W_RangeObject(W_BaseObject):
    classdef = ClassDef("Range", W_BaseObject.classdef)

    def __init__(self, w_start, w_end, inclusive):
        self.w_start = w_start
        self.w_end = w_end
        self.inclusive = inclusive

    @classdef.method("begin")
    def method_begin(self, space):
        return self.w_start

    @classdef.method("end")
    def method_end(self, space):
        return self.w_end
