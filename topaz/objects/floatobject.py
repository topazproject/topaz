import operator
import math
import sys

from rpython.rlib.objectmodel import compute_hash
from rpython.rlib.rarithmetic import ovfcheck_float_to_int
from rpython.rlib.rbigint import rbigint
from rpython.rlib.rfloat import (formatd, DTSF_ADD_DOT_0,
    NAN, INFINITY, isfinite, round_away)

from topaz.error import RubyError
from topaz.module import ClassDef
from topaz.objects.exceptionobject import W_ArgumentError
from topaz.objects.objectobject import W_RootObject
from topaz.objects.numericobject import W_NumericObject


class FloatStorage(object):
    def __init__(self, space):
        self.storages = {}

    def get_or_create(self, space, floatvalue):
        try:
            storage = self.storages[floatvalue]
        except KeyError:
            self.storages[floatvalue] = storage = space.send(space.w_object, "new")
        return storage


class W_FloatObject(W_RootObject):
    _immutable_fields_ = ["floatvalue"]

    classdef = ClassDef("Float", W_NumericObject.classdef)

    def __init__(self, space, floatvalue):
        self.floatvalue = floatvalue

    def __deepcopy__(self, memo):
        obj = super(W_FloatObject, self).__deepcopy__(memo)
        obj.floatvalue = self.floatvalue
        return obj

    def float_w(self, space):
        return self.floatvalue

    def bigint_w(self, space):
        return rbigint.fromfloat(self.floatvalue)

    @staticmethod
    def float_to_w_int(space, floatvalue):
        try:
            # the extra case makes sure that this method returns
            # bignums for the same numbers as the parser does.
            # this is checked in rubyspecs
            if floatvalue < 0:
                return space.newint(-ovfcheck_float_to_int(-floatvalue))
            else:
                return space.newint(ovfcheck_float_to_int(floatvalue))
        except OverflowError:
            return space.newbigint_fromfloat(floatvalue)

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        space.set_const(w_cls, "MAX", space.newfloat(sys.float_info.max))
        space.set_const(w_cls, "MIN", space.newfloat(sys.float_info.min))
        space.set_const(w_cls, "INFINITY", space.newfloat(INFINITY))
        space.set_const(w_cls, "NAN", space.newfloat(NAN))
        space.set_const(w_cls, "DIG", space.newint(sys.float_info.dig))
        space.set_const(w_cls, "EPSILON", space.newfloat(sys.float_info.epsilon))
        space.set_const(w_cls, "MANT_DIG", space.newint(sys.float_info.mant_dig))
        space.set_const(w_cls, "MAX_10_EXP", space.newint(sys.float_info.max_10_exp))
        space.set_const(w_cls, "MIN_10_EXP", space.newint(sys.float_info.min_10_exp))
        space.set_const(w_cls, "MAX_EXP", space.newint(sys.float_info.max_exp))
        space.set_const(w_cls, "MIN_EXP", space.newint(sys.float_info.min_exp))
        space.set_const(w_cls, "RADIX", space.newint(sys.float_info.radix))

    def find_instance_var(self, space, name):
        storage = space.fromcache(FloatStorage).get_or_create(space, self.floatvalue)
        return storage.find_instance_var(space, name)

    def set_instance_var(self, space, name, w_value):
        storage = space.fromcache(FloatStorage).get_or_create(space, self.floatvalue)
        storage.set_instance_var(space, name, w_value)

    def set_flag(self, space, name):
        storage = space.fromcache(FloatStorage).get_or_create(space, self.floatvalue)
        storage.set_flag(space, name)

    def unset_flag(self, space, name):
        storage = space.fromcache(FloatStorage).get_or_create(space, self.floatvalue)
        storage.unset_flag(space, name)

    def get_flag(self, space, name):
        storage = space.fromcache(FloatStorage).get_or_create(space, self.floatvalue)
        return storage.get_flag(space, name)

    @classdef.method("inspect")
    @classdef.method("to_s")
    def method_to_s(self, space):
        if math.isinf(self.floatvalue):
            if self.floatvalue >= 0:
                return space.newstr_fromstr("Infinity")
            else:
                return space.newstr_fromstr("-Infinity")
        elif math.isnan(self.floatvalue):
            return space.newstr_fromstr("NaN")
        else:
            # Uses the fact, that formatd mode "r" rounds as Ruby 1.9.3 does
            float_string = formatd(self.floatvalue, "r", 0, DTSF_ADD_DOT_0)
            if "e" in float_string:
                number, exponent = float_string.split("e")
                exponent = int(exponent)

                decimal_places = ""
                if "." in number:
                    number, decimal_places = number.split(".")

                if exponent < 0:
                    if decimal_places == "":
                        decimal_places = "0"
                    exponent_str = str(abs(exponent))
                    if len(exponent_str) == 1:
                        exponent_str = "0" + exponent_str

                    float_string = (number
                                    + "." + decimal_places
                                    + "e-" + exponent_str)
                elif exponent > 0:
                    # We have to move the decimal separator
                    # exponent steps to the right
                    if len(decimal_places) < exponent:
                        zeroes = "0" * (exponent - len(decimal_places))
                        decimal_places = (decimal_places + zeroes)

                    float_string = number + decimal_places + ".0"

            return space.newstr_fromstr(float_string)

    @classdef.method("to_f")
    def method_to_f(self, space):
        return self

    @classdef.method("to_i")
    def method_to_i(self, space):
        if math.isnan(self.floatvalue) or math.isinf(self.floatvalue):
            raise space.error(
                space.w_FloatDomainError,
                space.str_w(space.send(self, "to_s"))
            )
        return self.float_to_w_int(space, self.floatvalue)

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
            else:
                inf = math.copysign(INFINITY, other)
                if self.floatvalue < 0.0:
                    return space.newfloat(-inf)
                else:
                    return space.newfloat(inf)
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
    method_gt = new_bool_op(classdef, ">", operator.gt)
    method_gte = new_bool_op(classdef, ">=", operator.ge)

    @classdef.method("==")
    def method_eq(self, space, w_other):
        if space.is_kind_of(w_other, space.w_float):
            return space.newbool(self.floatvalue == space.float_w(w_other))

        try:
            return W_NumericObject.retry_binop_coercing(space, self, w_other, "==")
        except RubyError as e:
            if isinstance(e.w_value, W_ArgumentError):
                space.mark_topframe_not_escaped()
                return space.send(w_other, "==", [self])
            else:
                raise

    @classdef.method("equal?")
    def method_equalp(self, space, w_other):
        if space.is_kind_of(w_other, space.w_float):
            other = space.float_w(w_other)
            return space.newbool(
                self.floatvalue == other or
                (math.isnan(self.floatvalue) and math.isnan(other))
            )

        try:
            return W_NumericObject.retry_binop_coercing(space, self, w_other, "equal?")
        except RubyError as e:
            if isinstance(e.w_value, W_ArgumentError):
                space.mark_topframe_not_escaped()
                return space.send(w_other, "equal?", [self])
            else:
                raise

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

    @classdef.method("floor")
    def method_floor(self, space):
        return space.newint(int(math.floor(self.floatvalue)))

    @classdef.method("coerce")
    def method_coerce(self, space, w_other):
        if space.getclass(w_other) is space.getclass(self):
            return space.newarray([w_other, self])
        else:
            return space.newarray([space.send(self, "Float", [w_other]), self])

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
                    raise space.error(
                        space.w_NotImplementedError,
                        "Complex numbers as results"
                    )
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

    @classdef.method("floor")
    def method_floor(self, space):
        return self.float_to_w_int(space, math.floor(self.floatvalue))

    @classdef.method("ceil")
    def method_ceil(self, space):
        return self.float_to_w_int(space, math.ceil(self.floatvalue))

    @classdef.method("infinite?")
    def method_infinity(self, space):
        if math.isinf(self.floatvalue):
            return space.newint(int(math.copysign(1, self.floatvalue)))
        return space.w_nil

    @classdef.method("finite?")
    def method_finite(self, space):
        return space.newbool(isfinite(self.floatvalue))

    @classdef.method("nan?")
    def method_nan(self, space):
        return space.newbool(math.isnan(self.floatvalue))

    @classdef.method("round")
    def method_round(self, space):
        return space.newint(int(round_away(self.floatvalue)))

    @classdef.method("quo")
    def method_quo(self, space):
        raise space.error(space.w_NotImplementedError, "Numeric#quo")

    @classdef.method("divmod")
    def method_divmod(self, space, w_other):
        if math.isnan(self.floatvalue) or math.isinf(self.floatvalue):
            raise space.error(
                space.w_FloatDomainError,
                space.obj_to_s(space.getclass(w_other))
            )
        if (space.is_kind_of(w_other, space.w_fixnum) or
            space.is_kind_of(w_other, space.w_bignum) or
            space.is_kind_of(w_other, space.w_float)):
            y = space.float_w(w_other)
            if math.isnan(y):
                raise space.error(
                    space.w_FloatDomainError,
                    space.obj_to_s(space.getclass(w_other))
                )
            x = self.floatvalue
            mod = space.float_w(self.method_mod_float_impl(space, y))
            # TAKEN FROM: pypy/module/cpytext/floatobject.py
            div = (x - mod) / y
            if (mod):
                # ensure the remainder has the same sign as the denominator
                if ((y < 0.0) != (mod < 0.0)):
                    mod += y
                    div -= 1.0
            else:
                mod *= mod  # hide "mod = +0" from optimizer
                if y < 0.0:
                    mod = -mod
            # snap quotient to nearest integral value
            if div:
                floordiv = math.floor(div)
                if (div - floordiv > 0.5):
                    floordiv += 1.0
            else:
                # div is zero - get the same sign as the true quotient
                div *= div  # hide "div = +0" from optimizers
                floordiv = div * x / y  # zero w/ sign of vx/wx
            try:
                return space.newarray([self.float_to_w_int(space, round_away(div)), space.newfloat(mod)])
            except OverflowError:
                return space.newarray([space.newbigint_fromfloat(div), space.newfloat(mod)])
        else:
            raise space.error(
                space.w_TypeError,
                "%s can't be coerced into Float" % (
                    space.obj_to_s(space.getclass(w_other))
                )
            )

    @classdef.method("%")
    @classdef.method("modulo")
    def method_mod(self, space, w_other):
        if (space.is_kind_of(w_other, space.w_fixnum) or
            space.is_kind_of(w_other, space.w_bignum) or
            space.is_kind_of(w_other, space.w_float)):
            return self.method_mod_float_impl(space, space.float_w(w_other))
        else:
            raise space.error(
                space.w_TypeError,
                "%s can't be coerced into Float" % (
                    space.obj_to_s(space.getclass(w_other))
                )
            )

    def method_mod_float_impl(self, space, other):
        if other == 0.0:
            raise space.error(space.w_ZeroDivisionError, "divided by 0")
        elif self.floatvalue == -0.0:
            return space.newfloat(-0.0)
        elif math.isinf(other) and other < 0.0:
            return space.newfloat(other)
        elif math.isnan(self.floatvalue) or math.isinf(self.floatvalue):
            return space.newfloat(NAN)
        return space.newfloat(math.fmod(self.floatvalue, other))
