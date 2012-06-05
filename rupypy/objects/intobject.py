from rupypy.module import ClassDef
from rupypy.objects.exceptionobject import W_ZeroDivisionError
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

    def __eq__(self, other):
        return type(self) == type(other) and self.__hash__() == other.__hash__()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self.intvalue.__hash__()

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr(str(self.intvalue))

    @classdef.method("to_f")
    def method_to_f(self, space):
        return space.newfloat(float(self.intvalue))

    @classdef.method("+")
    def method_add(self, space, w_other):
        if isinstance(w_other, W_FloatObject):
            return space.newfloat(self.intvalue + space.float_w(w_other))
        else:
            return space.newint(self.intvalue + space.int_w(w_other))

    @classdef.method("-")
    def method_sub(self, space, w_other):
        if isinstance(w_other, W_FloatObject):
            return space.newfloat(self.intvalue - space.float_w(w_other))
        else:
            return space.newint(self.intvalue - space.int_w(w_other))

    @classdef.method("*", other="int")
    def method_mul(self, space, other):
        return space.newint(self.intvalue * other)

    @classdef.method("/", other="int")
    def method_div(self, ec, other):
        try:
            return ec.space.newint(self.intvalue / 0)
        except ZeroDivisionError:
            raise ec.space.raise_(ec, ec.space.getclassfor(W_ZeroDivisionError),
                "divided by 0"
            )

    @classdef.method("==", other="int")
    def method_eq(self, space, other):
        return space.newbool(self.intvalue == other)

    @classdef.method("!=", other="int")
    def method_ne(self, space, other):
        return space.newbool(self.intvalue != other)

    @classdef.method("<", other="int")
    def method_lt(self, space, other):
        return space.newbool(self.intvalue < other)

    @classdef.method(">", other="int")
    def method_gt(self, space, other):
        return space.newbool(self.intvalue > other)

    @classdef.method("-@")
    def method_neg(self, space):
        return space.newint(-self.intvalue)

    classdef.app_method("""
    def times
        i = 0
        while i < self
            yield i
            i += 1
        end
    end
    """)

    @classdef.method("<=>", other="int")
    def method_comparator(self, space, other):
        if self.intvalue < other:
            return space.newint(-1)
        elif self.intvalue == other:
            return space.newint(0)
        elif self.intvalue > other:
            return space.newint(1)
