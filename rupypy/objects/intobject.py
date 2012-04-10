from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object


class W_IntObject(W_Object):
    classdef = ClassDef("Fixnum")

    def __init__(self, intvalue):
        self.intvalue = intvalue

    def int_w(self, space):
        return self.intvalue

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr([x for x in str(self.intvalue)])

    @classdef.method("+", other=int)
    def method_add(self, space, other):
        return space.newint(self.intvalue + other)

    @classdef.method("*", other=int)
    def method_mul(self, space, other):
        return space.newint(self.intvalue * other)