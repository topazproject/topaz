import math
import operator

from rpython.rlib import rfloat
from rpython.rlib.debug import check_regular_int
from rpython.rlib.objectmodel import specialize
from rpython.rlib.rarithmetic import (r_uint, r_longlong, r_ulonglong,
    ovfcheck, LONG_BIT)
from rpython.rlib.rbigint import rbigint
from rpython.rlib.rfloat import round_away
from rpython.rtyper.lltypesystem import lltype, rffi

from topaz.coerce import Coerce
from topaz.module import ClassDef
from topaz.objects.floatobject import W_FloatObject
from topaz.objects.integerobject import W_IntegerObject
from topaz.objects.numericobject import W_NumericObject
from topaz.objects.objectobject import W_RootObject
from topaz.system import IS_WINDOWS


class FixnumStorage(object):
    def __init__(self, space):
        self.storages = {}

    def get_or_create(self, space, intvalue):
        try:
            storage = self.storages[intvalue]
        except KeyError:
            self.storages[intvalue] = storage = space.send(space.w_object, "new")
        return storage


class W_FixnumObject(W_RootObject):
    _immutable_fields_ = ["intvalue"]

    classdef = ClassDef("Fixnum", W_IntegerObject.classdef)

    def __init__(self, space, intvalue):
        check_regular_int(intvalue)
        self.intvalue = intvalue

    def __deepcopy__(self, memo):
        obj = super(W_FixnumObject, self).__deepcopy__(memo)
        obj.intvalue = self.intvalue
        return obj

    def int_w(self, space):
        return self.intvalue

    def bigint_w(self, space):
        return rbigint.fromint(self.intvalue)

    def float_w(self, space):
        return float(self.intvalue)

    def intmask_w(self, space):
        return self.intvalue

    def uintmask_w(self, space):
        return r_uint(self.intvalue)

    def longlongmask_w(self, space):
        return r_longlong(self.intvalue)

    def ulonglongmask_w(self, space):
        return r_ulonglong(self.intvalue)

    def find_instance_var(self, space, name):
        storage = space.fromcache(FixnumStorage).get_or_create(space, self.intvalue)
        return storage.find_instance_var(space, name)

    def set_instance_var(self, space, name, w_value):
        storage = space.fromcache(FixnumStorage).get_or_create(space, self.intvalue)
        storage.set_instance_var(space, name, w_value)

    def set_flag(self, space, name):
        storage = space.fromcache(FixnumStorage).get_or_create(space, self.intvalue)
        storage.set_flag(space, name)

    def unset_flag(self, space, name):
        storage = space.fromcache(FixnumStorage).get_or_create(space, self.intvalue)
        storage.unset_flag(space, name)

    def get_flag(self, space, name):
        storage = space.fromcache(FixnumStorage).get_or_create(space, self.intvalue)
        return storage.get_flag(space, name)

    @classdef.method("extend")
    @classdef.method("singleton_class")
    def method_singleton_class(self, space):
        raise space.error(space.w_TypeError, "can't define singleton")

    @classdef.method("inspect")
    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr(str(self.intvalue))

    @classdef.method("to_f")
    def method_to_f(self, space):
        return space.newfloat(float(self.intvalue))

    @classdef.method("to_i")
    @classdef.method("to_int")
    def method_to_i(self, space):
        return self

    def new_binop(classdef, name, func):
        @classdef.method(name)
        def method(self, space, w_other):
            if space.is_kind_of(w_other, space.w_fixnum):
                other = space.int_w(w_other)
                try:
                    value = ovfcheck(func(self.intvalue, other))
                except OverflowError:
                    return space.send(
                        space.newbigint_fromint(self.intvalue), name,
                        [w_other]
                    )
                else:
                    return space.newint(value)
            elif space.is_kind_of(w_other, space.w_bignum):
                return space.send(space.newbigint_fromint(self.intvalue), name, [w_other])
            elif space.is_kind_of(w_other, space.w_float):
                return space.newfloat(func(self.intvalue, space.float_w(w_other)))
            else:
                return W_NumericObject.retry_binop_coercing(space, self, w_other, name)
        method.__name__ = "method_%s" % func.__name__
        return method
    method_add = new_binop(classdef, "+", operator.add)
    method_sub = new_binop(classdef, "-", operator.sub)
    method_mul = new_binop(classdef, "*", operator.mul)
    method_pow = new_binop(classdef, "**", operator.pow)

    @classdef.method("floor")
    def method_floor(self, space):
        return self

    def raise_zero_division_error(self, space):
        raise space.error(space.w_ZeroDivisionError, "divided by 0")

    def divide(self, space, w_other):
        if space.is_kind_of(w_other, space.w_fixnum):
            other = space.int_w(w_other)
            try:
                return space.newint(self.intvalue / other)
            except ZeroDivisionError:
                self.raise_zero_division_error(space)
        elif space.is_kind_of(w_other, space.w_bignum):
            return space.send(space.newbigint_fromint(self.intvalue), "/", [w_other])
        elif space.is_kind_of(w_other, space.w_float):
            return space.send(space.newfloat(space.float_w(self)), "/", [w_other])
        else:
            return W_NumericObject.retry_binop_coercing(space, self, w_other, "/")

    @classdef.method("/")
    def method_divide(self, space, w_other):
        return self.divide(space, w_other)

    @classdef.method("div")
    def method_div(self, space, w_other):
        if space.is_kind_of(w_other, space.w_float):
            if space.float_w(w_other) == 0.0:
                self.raise_zero_division_error(space)
            else:
                w_float = space.send(
                    space.newfloat(space.float_w(self)),
                    "/",
                    [w_other]
                )
                w_float = space.newfloat(math.floor(Coerce.float(space, w_float)))
                return space.send(w_float, "to_i")
        else:
            return self.divide(space, w_other)

    @classdef.method("fdiv")
    def method_fdiv(self, space, w_other):
        if space.is_kind_of(w_other, space.w_fixnum):
            other = space.int_w(w_other)
            try:
                res = float(self.intvalue) / float(other)
            except ZeroDivisionError:
                return space.newfloat(rfloat.copysign(rfloat.INFINITY, float(self.intvalue)))
            else:
                return space.newfloat(res)
        elif space.is_kind_of(w_other, space.w_bignum):
            return space.send(space.newbigint_fromint(self.intvalue), "fdiv", [w_other])
        elif space.is_kind_of(w_other, space.w_float):
            other = space.float_w(w_other)
            try:
                res = float(self.intvalue) / other
            except ZeroDivisionError:
                return space.newfloat(rfloat.copysign(rfloat.INFINITY, float(self.intvalue)))
            else:
                return space.newfloat(res)
        else:
            return W_NumericObject.retry_binop_coercing(space, self, w_other, "fdiv")

    @classdef.method("**")
    def method_pow(self, space, w_other):
        if space.is_kind_of(w_other, space.w_fixnum):
            return self.method_pow_int_impl(space, w_other)
        elif space.getclass(w_other) is space.w_float:
            return space.send(
                space.newfloat(float(self.intvalue)), "**", [w_other]
            )
        elif space.getclass(w_other) is space.w_bignum:
            return space.send(
                space.newbigint_fromint(self.intvalue), "**",
                [w_other]
            )
        else:
            raise space.error(space.w_TypeError,
                "%s can't be coerced into Fixnum" % space.obj_to_s(space.getclass(w_other))
            )

    def method_pow_int_impl(self, space, w_other):
        exp = space.int_w(w_other)
        temp = self.intvalue
        if exp > 0:
            ix = 1
            try:
                while exp > 0:
                    if exp & 1:
                        ix = ovfcheck(ix * temp)
                    exp >>= 1
                    if exp == 0:
                        break
                    temp = ovfcheck(temp * temp)
            except OverflowError:
                return space.send(
                    space.newbigint_fromint(self.intvalue), "**",
                    [w_other]
                )
            return space.newint(ix)
        else:
            return space.send(space.newfloat(float(temp)), "**", [w_other])

    @classdef.method("divmod")
    def method_divmod(self, space, w_other):
        if space.is_kind_of(w_other, space.w_float):
            return space.send(self.method_to_f(space), "divmod", [w_other])
        elif space.is_kind_of(w_other, space.w_bignum):
            return space.send(space.newbigint_fromint(self.intvalue), "divmod", [w_other])
        elif space.is_kind_of(w_other, space.w_fixnum):
            y = space.int_w(w_other)
            if y == 0:
                raise space.error(
                    space.w_ZeroDivisionError,
                    "divided by 0"
                )
            mod = space.int_w(self.method_mod_int_impl(space, y))
            div = (self.intvalue - mod) / y
            return space.newarray([space.newint(int(round_away(div))), space.newfloat(mod)])
        else:
            raise space.error(
                space.w_TypeError,
                "%s can't be coerced into Fixnum" % (
                    space.obj_to_s(space.getclass(w_other))
                )
            )

    @classdef.method("%")
    @classdef.method("modulo")
    def method_mod(self, space, w_other):
        if space.is_kind_of(w_other, space.w_fixnum):
            return self.method_mod_int_impl(space, space.int_w(w_other))
        elif space.is_kind_of(w_other, space.w_float):
            return space.send(self.method_to_f(space), "%", [w_other])
        elif space.is_kind_of(w_other, space.w_bignum):
            return space.send(space.newbigint_fromint(self.intvalue), "%", [w_other])
        else:
            raise space.error(
                space.w_TypeError,
                "%s can't be coerced into Fixnum" % (
                    space.obj_to_s(space.getclass(w_other))
                )
            )

    def method_mod_int_impl(self, space, other):
        if other == 0:
            raise space.error(space.w_ZeroDivisionError, "divided by 0")
        return space.newint(self.intvalue % other)

    @classdef.method("<<", other="int")
    def method_left_shift(self, space, other):
        if other < 0:
            return space.newint(self.intvalue >> -other)
        elif other >= LONG_BIT:
            return space.send(
                space.newbigint_fromint(self.intvalue), "<<",
                [space.newint(other)]
            )
        else:
            try:
                value = ovfcheck(self.intvalue << other)
            except OverflowError:
                return space.send(
                    space.newbigint_fromint(self.intvalue), "<<",
                    [space.newint(other)]
                )
            else:
                return space.newint(value)

    @classdef.method(">>", other="int")
    def method_right_shift(self, space, other):
        if other < 0:
            return space.newint(self.intvalue << -other)
        else:
            return space.newint(self.intvalue >> other)

    def new_bitwise_op(classdef, name, func):
        @classdef.method(name)
        def method(self, space, w_other):
            w_other = space.convert_type(w_other, space.w_integer, "to_int")
            if space.is_kind_of(w_other, space.w_fixnum):
                other = space.int_w(w_other)
                return space.newint(func(self.intvalue, other))
            elif space.is_kind_of(w_other, space.w_bignum):
                return space.send(space.newbigint_fromint(self.intvalue), name, [w_other])
            else:
                return W_NumericObject.retry_binop_coercing(space, self, w_other, name)
        method.__name__ = "method_%s" % func.__name__
        return method
    method_and = new_bitwise_op(classdef, "&", operator.and_)
    method_or = new_bitwise_op(classdef, "|", operator.or_)
    method_xor = new_bitwise_op(classdef, "^", operator.xor)

    @classdef.method("~")
    def method_invert(self, space):
        return space.newint(~self.intvalue)

    @classdef.method("==")
    @classdef.method("equal?")
    def method_eq(self, space, w_other):
        if isinstance(w_other, W_FixnumObject):
            return space.newbool(self.comparator(space, space.int_w(w_other)) == 0)
        elif isinstance(w_other, W_FloatObject):
            return space.newbool(self.comparator(space, space.float_w(w_other)) == 0)
        else:
            return space.send(w_other, "==", [self])

    @classdef.method("!=")
    def method_ne(self, space, w_other):
        return space.newbool(space.send(self, "==", [w_other]) is space.w_false)

    def new_bool_op(classdef, name, func):
        @classdef.method(name)
        def method(self, space, w_other):
            if space.is_kind_of(w_other, space.w_float):
                return space.newbool(func(self.intvalue, space.float_w(w_other)))
            elif space.is_kind_of(w_other, space.w_fixnum):
                return space.newbool(func(self.intvalue, space.int_w(w_other)))
            else:
                return W_NumericObject.retry_binop_coercing(space, self, w_other, name, raise_error=True)
        method.__name__ = "method_%s" % func.__name__
        return method
    method_lt = new_bool_op(classdef, "<", operator.lt)
    method_lte = new_bool_op(classdef, "<=", operator.le)
    method_gt = new_bool_op(classdef, ">", operator.gt)
    method_gte = new_bool_op(classdef, ">=", operator.ge)

    @classdef.method("<=>")
    def method_comparator(self, space, w_other):
        if isinstance(w_other, W_FixnumObject):
            return space.newint(self.comparator(space, space.int_w(w_other)))
        elif isinstance(w_other, W_FloatObject):
            return space.newint(self.comparator(space, space.float_w(w_other)))
        else:
            return space.w_nil

    @specialize.argtype(2)
    def comparator(self, space, other):
        if self.intvalue < other:
            return -1
        elif self.intvalue == other:
            return 0
        elif self.intvalue > other:
            return 1
        return 1

    @classdef.method("hash")
    def method_hash(self, space):
        return self

    if IS_WINDOWS:
        @classdef.method("size")
        def method_size(self, space):
            # RPython translation is always 32bit on Windows
            return space.newint(4)
    else:
        @classdef.method("size")
        def method_size(self, space):
            return space.newint(rffi.sizeof(lltype.typeOf(self.intvalue)))

    @classdef.method("coerce")
    def method_coerce(self, space, w_other):
        if space.getclass(w_other) is space.getclass(self):
            return space.newarray([w_other, self])
        else:
            return space.newarray([space.send(self, "Float", [w_other]), self])

    @classdef.method("chr")
    def method_chr(self, space):
        if self.intvalue > 255 or self.intvalue < 0:
            raise space.error(space.w_RangeError, "%d out of char range" % self.intvalue)
        else:
            return space.newstr_fromstr(chr(self.intvalue))

    @classdef.method("[]", idx="int")
    def method_subscript(self, space, idx):
        if not 0 <= idx < LONG_BIT:
            return space.newint(0)
        return space.newint(int(bool(self.intvalue & (1 << idx))))


class W_MutableFixnumObject(W_FixnumObject):
    _immutable_fields_ = []

    def set_intvalue(self, intvalue):
        check_regular_int(intvalue)
        self.intvalue = intvalue
