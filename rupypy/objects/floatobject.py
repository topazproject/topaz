from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_BaseObject


class W_FloatObject(W_BaseObject):
    _immutable_fields_ = ["floatvalue"]

    classdef = ClassDef("Float", W_BaseObject.classdef)

    def __init__(self, floatvalue):
        self.floatvalue = floatvalue

    def float_w(self, space):
        return self.floatvalue

    def __eq__(self, other):
        return type(self) == type(other) and self.__hash__() == other.__hash__()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self.floatvalue.__hash__()

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr(str(self.floatvalue))

    @classdef.method("to_f")
    def method_to_f(self, space):
        return self

    @classdef.method("-@")
    def method_neg(self, space):
        return space.newfloat(-self.floatvalue)

    @classdef.method("+", other="float")
    def method_add(self, space, other):
        return space.newfloat(self.floatvalue + other)

    @classdef.method("-", other="float")
    def method_sub(self, space, other):
        return space.newfloat(self.floatvalue - other)

    @classdef.method("*", other="float")
    def method_mul(self, space, other):
        return space.newfloat(self.floatvalue * other)

    @classdef.method("/", other="float")
    def method_div(self, space, other):
        return space.newfloat(self.floatvalue / other)
