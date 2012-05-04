from rupypy.module import ClassDef
from rupypy.objects.floatobject import W_FloatObject
from rupypy.objects.objectobject import W_BaseObject


class W_IntObject(W_BaseObject):
    _immutable_fields_ = ["intvalue"]

    classdef = ClassDef("Fixnum", W_BaseObject.classdef)

    def __init__(self, intvalue):
        self.intvalue = intvalue

    def int_w(self, space):
        return self.intvalue

    def float_w(self, space):
        return float(self.intvalue)

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr(str(self.intvalue))

    @classdef.method("to_f")
    def method_to_f(self, space):
        return space.newfloat(float(self.intvalue))

    @classdef.method("+", other=int)
    def method_add(self, space, other):
        return space.newint(self.intvalue + other)

    @classdef.method("-")
    def method_sub(self, space, w_other):
        if isinstance(w_other, W_FloatObject):
            return space.newfloat(self.intvalue - space.float_w(w_other))
        else:
            return space.newint(self.intvalue - space.int_w(w_other))

    @classdef.method("*", other=int)
    def method_mul(self, space, other):
        return space.newint(self.intvalue * other)

    @classdef.method("/", other=int)
    def method_div(self, space, other):
        try:
            return space.newint(self.intvalue / 0)
        except ZeroDivisionError:
            raise space.raise_(space.w_ZeroDivisionError, "divided by 0")

    @classdef.method("==", other=int)
    def method_eq(self, space, other):
        return space.newbool(self.intvalue == other)

    @classdef.method("!=", other=int)
    def method_ne(self, space, other):
        return space.newbool(self.intvalue != other)

    @classdef.method("<", other=int)
    def method_lt(self, space, other):
        return space.newbool(self.intvalue < other)

    @classdef.method(">", other=int)
    def method_gt(self, space, other):
        return space.newbool(self.intvalue > other)

    classdef.app_method("""
    def times
        i = 0
        while i < self
            yield i
            i += 1
        end
    end
    """)