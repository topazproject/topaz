import operator

from pypy.rlib.objectmodel import compute_hash

from rupypy.module import ClassDef
from rupypy.objects.numericobject import W_NumericObject


class W_FloatObject(W_NumericObject):
    _immutable_fields_ = ["floatvalue"]

    classdef = ClassDef("Float", W_NumericObject.classdef)

    def __init__(self, space, floatvalue):
        W_NumericObject.__init__(self, space)
        self.floatvalue = floatvalue

    def __deepcopy__(self, memo):
        obj = super(W_FloatObject, self).__deepcopy__(memo)
        obj.floatvalue = self.floatvalue
        return obj

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

    def new_bool_op(classdef, name, func):
        @classdef.method(name)
        def method(self, space, w_other):
            if space.is_kind_of(w_other, space.w_float):
                return space.newbool(func(self.floatvalue, space.float_w(w_other)))
            else:
                return W_NumericObject.retry_binop_coercing(space, self, w_other, name)
        method.__name__ = "method_%s" % func.__name__
        return method
    method_lt = new_bool_op(classdef, "<", operator.lt)
    method_lte = new_bool_op(classdef, "<=", operator.le)
    method_eq = new_bool_op(classdef, "==", operator.eq)

    @classdef.method("hash")
    def method_hash(self, space):
        return space.newint(compute_hash(self.floatvalue))

    @classdef.method("abs")
    def method_abs(self, space):
        return space.newfloat(abs(self.floatvalue))
