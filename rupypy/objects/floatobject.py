from pypy.rlib.objectmodel import compute_hash

from rupypy.module import ClassDef
from rupypy.objects.numericobject import W_NumericObject


class W_FloatObject(W_NumericObject):
    _immutable_fields_ = ["floatvalue"]

    classdef = ClassDef("Float", W_NumericObject.classdef)

    def __init__(self, space, floatvalue):
        W_NumericObject.__init__(self, space)
        self.floatvalue = floatvalue

    def float_w(self, space):
        return self.floatvalue

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr(str(self.floatvalue))

    @classdef.method("to_f")
    def method_to_f(self, space):
        return self

    @classdef.method("to_i")
    def method_to_i(self, space):
        return space.newint(int(self.floatvalue))

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

    @classdef.method("<=")
    def method_lte(self, space, w_other):
        if isinstance(w_other, W_FloatObject):
            return space.newbool(space.float_w(self) <= space.float_w(w_other))
        else:
            return W_NumericObject.retry_binop_coercing(space, self, w_other, "<=", raise_error=True)

    @classdef.method("==", other="float")
    def method_eq(self, space, other):
        return space.newbool(self.floatvalue == other)

    @classdef.method("hash")
    def method_hash(self, space):
        return space.newint(compute_hash(self.floatvalue))
