from topaz.module import ClassDef
from topaz.modules.enumerable import Enumerable
from topaz.objects.objectobject import W_Object


class W_RangeObject(W_Object):
    classdef = ClassDef("Range", W_Object.classdef, filepath=__file__)
    classdef.include_module(Enumerable)

    def __init__(self, space, w_start, w_end, exclusive):
        W_Object.__init__(self, space)
        self.w_start = w_start
        self.w_end = w_end
        self.exclusive = exclusive

    @classdef.method("first")
    @classdef.method("begin")
    def method_begin(self, space):
        return self.w_start

    @classdef.method("last")
    @classdef.method("end")
    def method_end(self, space):
        return self.w_end

    @classdef.method("exclude_end?")
    def method_exclude_end(self, space):
        return space.newbool(self.exclusive)
        
    @classdef.method("to_a")
    def method_to_a(self, space):
        start, end = space.int_w(self.w_start), space.int_w(self.w_end)
        if not self.exclusive:
            end += 1
        return space.newarray([space.newint(i) for i in range(start, end)])
