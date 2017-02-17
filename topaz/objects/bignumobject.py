from rpython.rlib.rbigint import rbigint
from rpython.rlib.rfloat import INFINITY
from rpython.rtyper.lltypesystem import lltype, rffi

from topaz.module import ClassDef
from topaz.objects.integerobject import W_IntegerObject
from topaz.objects.numericobject import W_NumericObject


class W_BignumObject(W_IntegerObject):
    classdef = ClassDef("Bignum", W_IntegerObject.classdef)
    _immutable_fields_ = ["bigint"]

    def __init__(self, space, bigint):
        W_IntegerObject.__init__(self, space)
        self.bigint = bigint

    @staticmethod
    def newbigint_fromint(space, intvalue):
        return W_BignumObject(space, rbigint.fromint(intvalue))

    @staticmethod
    def newbigint_fromfloat(space, floatvalue):
        return W_BignumObject(space, rbigint.fromfloat(floatvalue))

    @staticmethod
    def newbigint_fromrbigint(space, bigint):
        return W_BignumObject(space, bigint)

    def int_w(self, space):
        try:
            return self.bigint.toint()
        except OverflowError:
            raise space.error(space.w_RangeError, "bignum too big to convert into `long'")

    def bigint_w(self, space):
        return self.bigint

    def float_w(self, space):
        return self.bigint.tofloat()

    def intmask_w(self, space):
        return rffi.cast(lltype.Signed, self.uintmask_w((space)))

    def uintmask_w(self, space):
        return self.bigint.uintmask()

    def longlongmask_w(self, space):
        return rffi.cast(lltype.SignedLongLong, self.ulonglongmask_w((space)))

    def ulonglongmask_w(self, space):
        return self.bigint.ulonglongmask()

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr(self.bigint.str())

    @classdef.method("to_f")
    def method_to_f(self, space):
        return space.newfloat(self.bigint.tofloat())

    @classdef.method("+", other="bigint")
    def method_plus(self, space, other):
        return space.newbigint_fromrbigint(self.bigint.add(other))

    @classdef.method("-", other="bigint")
    def method_sub(self, space, other):
        return space.newbigint_fromrbigint(self.bigint.sub(other))

    @classdef.method("*", other="bigint")
    def method_times(self, space, other):
        return space.newbigint_fromrbigint(self.bigint.mul(other))

    def floordiv(self, space, other):
        try:
            result = self.bigint.div(other)
        except ZeroDivisionError:
            raise space.error(space.w_ZeroDivisionError, "divided by 0")
        try:
            return space.newint(result.toint())
        except OverflowError:
            return space.newbigint_fromrbigint(result)

    @classdef.method("/")
    def method_divide(self, space, w_other):
        if space.is_kind_of(w_other, space.w_fixnum):
            return self.floordiv(space, rbigint.fromint(space.int_w(w_other)))
        elif space.is_kind_of(w_other, space.w_bignum):
            return self.floordiv(space, space.bigint_w(w_other))
        elif space.is_kind_of(w_other, space.w_float):
            return space.send(space.newfloat(space.float_w(self)), "/", [w_other])
        else:
            return W_NumericObject.retry_binop_coercing(space, self, w_other, "/")

    @classdef.method("fdiv")
    def method_fdiv(self, space, w_other):
        raise space.error(space.w_NotImplementedError, "Bignum#fdiv")

    @classdef.method("<<", other="int")
    def method_left_shift(self, space, other):
        if other >= 0:
            return space.newbigint_fromrbigint(self.bigint.lshift(other))
        else:
            return space.newbigint_fromrbigint(self.bigint.rshift(-other))

    @classdef.method("&", other="bigint")
    def method_and(self, space, other):
        return space.newbigint_fromrbigint(self.bigint.and_(other))

    @classdef.method("|", other="bigint")
    def method_or(self, space, other):
        return space.newbigint_fromrbigint(self.bigint.or_(other))

    @classdef.method("^", other="bigint")
    def method_xor(self, space, other):
        return space.newbigint_fromrbigint(self.bigint.xor(other))

    @classdef.method("==", other="bigint")
    def method_eq(self, space, other):
        return space.newbool(self.bigint.eq(other))

    @classdef.method("<=>", other="bigint")
    def method_comparator(self, space, other):
        if self.bigint.gt(other):
            return space.newint(1)
        elif self.bigint.eq(other):
            return space.newint(0)
        elif self.bigint.lt(other):
            return space.newint(-1)

    @classdef.method("hash")
    def method_hash(self, space):
        return space.newint(self.bigint.hash())

    @classdef.method("coerce")
    def method_coerce(self, space, w_other):
        if isinstance(w_other, W_BignumObject):
            return space.newarray([w_other, self])
        elif space.getclass(w_other) is space.w_fixnum:
            return space.newarray([
                space.newbigint_fromint(space.int_w(w_other)),
                self,
            ])
        else:
            raise space.error(space.w_TypeError,
                "can't coerce %s to Bignum" %
                    space.obj_to_s(space.getclass(w_other))
            )

    @classdef.method("**")
    def method_pow(self, space, w_other):
        if space.getclass(w_other) is space.w_fixnum or space.getclass(w_other) is space.w_bignum:
            exp = space.bigint_w(w_other)
            negative_exponent = False
            if exp.sign < 0:
                negative_exponent = True
                exp = exp.abs()
            result = self.bigint.pow(exp, None)
            if negative_exponent:
                return space.newfloat(1.0 / result.tofloat())
            else:
                return space.newbigint_fromrbigint(result)
        elif space.getclass(w_other) is space.w_float:
            try:
                float_value = space.float_w(self)
            except OverflowError:
                return space.newfloat(INFINITY)
            return space.send(
                space.newfloat(float_value),
                "**",
                [w_other]
            )
        else:
            raise space.error(
                space.w_TypeError,
                "%s can't be coerced into Bignum" % (
                    space.obj_to_s(space.getclass(w_other))
                )
            )

    @classdef.method("divmod")
    def method_divmod(self, space, w_other):
        if space.is_kind_of(w_other, space.w_float):
            return space.send(self.method_to_f(space), "divmod", [w_other])
        elif(space.is_kind_of(w_other, space.w_bignum) or
             space.is_kind_of(w_other, space.w_fixnum)):
            other = space.bigint_w(w_other)
            if not other.tobool():
                raise space.error(space.w_ZeroDivisionError, "divided by 0")
            div, mod = self.bigint.divmod(other)
            return space.newarray([space.newbigint_fromrbigint(div),
                                   space.newbigint_fromrbigint(mod)])
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
        if space.getclass(w_other) is space.w_fixnum:
            return space.newint(
                space.int_w(
                    self.method_mod_bigint_impl(
                        space,
                        space.bigint_w(w_other)
                    )
                )
            )
        elif space.getclass(w_other) is space.w_float:
            return space.send(self.method_to_f(space), "%", [w_other])
        elif space.getclass(w_other) is space.w_bignum:
            return self.method_mod_bigint_impl(space, space.bigint_w(w_other))
        else:
            raise space.error(
                space.w_TypeError,
                "%s can't be coerced into Fixnum" % (
                    space.obj_to_s(space.getclass(w_other))
                )
            )

    def method_mod_bigint_impl(self, space, other):
        if not other.tobool():
            raise space.error(space.w_ZeroDivisionError, "divided by 0")
        return space.newbigint_fromrbigint(self.bigint.mod(other))
