import operator
import math
import sys

from rpython.rlib.objectmodel import compute_hash
from rpython.rlib.rfloat import NAN, INFINITY

from topaz.module import ClassDef
from topaz.objects.numericobject import W_NumericObject


class W_FloatObject(W_NumericObject):
    _immutable_fields_ = ["floatvalue"]

    classdef = ClassDef("Float", W_NumericObject.classdef, filepath=__file__)

    def __init__(self, space, floatvalue):
        W_NumericObject.__init__(self, space)
        self.floatvalue = floatvalue

    def __deepcopy__(self, memo):
        obj = super(W_FloatObject, self).__deepcopy__(memo)
        obj.floatvalue = self.floatvalue
        return obj

    def float_w(self, space):
        return self.floatvalue

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        space.set_const(w_cls, "MAX", space.newfloat(sys.float_info.max))
        space.set_const(w_cls, "MIN", space.newfloat(sys.float_info.min))

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
        if other == 0.0:
            if self.floatvalue == 0.0:
                return space.newfloat(NAN)
            elif self.floatvalue < 0.0:
                return space.newfloat(-INFINITY)
            else:
                return space.newfloat(INFINITY)
        else:
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
    method_gt = new_bool_op(classdef, ">", operator.gt)
    method_gte = new_bool_op(classdef, ">=", operator.ge)

    @classdef.method("<=>")
    def method_comparator(self, space, w_other):
        if space.is_kind_of(w_other, space.w_numeric):
            other = space.float_w(w_other)
            if self.floatvalue < other:
                return space.newint(-1)
            elif self.floatvalue == other:
                return space.newint(0)
            elif self.floatvalue > other:
                return space.newint(1)
            return space.newint(1)
        else:
            return space.w_nil

    @classdef.method("hash")
    def method_hash(self, space):
        return space.newint(compute_hash(self.floatvalue))

    @classdef.method("abs")
    def method_abs(self, space):
        return space.newfloat(abs(self.floatvalue))

    @classdef.method("**")
    def method_pow(self, space, w_other):
        if space.is_kind_of(w_other, space.w_numeric):
            x = self.floatvalue
            y = space.float_w(w_other)
            negate_result = False

            if y == 2.0:
                return space.newfloat(x * x)
            elif y == 0.0:
                return space.newfloat(1.0)
            elif math.isnan(x):
                return space.newfloat(x)
            elif math.isnan(y):
                if x == 1.0:
                    return space.newfloat(1.0)
                elif x < 0.0:
                    raise NotImplementedError("Complex numbers as results")
                else:
                    return space.newfloat(y)
            elif math.isinf(y):
                if x == 1.0 or x == -1.0:
                    return space.newfloat(x)
                elif x < -1.0 or x > 1.0:
                    return space.newfloat(INFINITY if y > 0.0 else 0.0)
                else:
                    return space.newfloat(0.0 if y > 0.0 else INFINITY)
            elif x == 0.0 and y < 0.0:
                return space.newfloat(INFINITY)

            if x < 0.0:
                x = -x
                negate_result = math.fmod(abs(y), 2.0) == 1.0

            if math.isinf(x):
                if y > 0.0:
                    return space.newfloat(-INFINITY if negate_result else INFINITY)
                else:
                    return space.newfloat(-0.0 if negate_result else 0.0)
            elif x == 1.0:
                return space.newfloat(-1.0 if negate_result else 1.0)
            else:
                try:
                    # OverflowError raised in math.pow, but not overflow.pow
                    z = math.pow(x, y)
                except OverflowError:
                    return space.newfloat(-INFINITY if negate_result else INFINITY)
                except ValueError:
                    return space.newfloat(NAN)
                return space.newfloat(-z if negate_result else z)
        else:
            raise space.error(
                space.w_TypeError,
                "%s can't be coerced into Float" % space.getclass(w_other).name
            )
