from pypy.rlib.rbigint import rbigint
from pypy.rlib.rfloat import INFINITY

from rupypy.module import ClassDef
from rupypy.objects.integerobject import W_IntegerObject


class W_BignumObject(W_IntegerObject):
    classdef = ClassDef("Bignum", W_IntegerObject.classdef, filepath=__file__)

    def __init__(self, space, bigint):
        W_IntegerObject.__init__(self, space)
        self.bigint = bigint

    @staticmethod
    def newbigint_fromint(space, intvalue):
        return W_BignumObject(space, rbigint.fromint(intvalue))

    @staticmethod
    def newbigint_fromrbigint(space, bigint):
        return W_BignumObject(space, bigint)

    def int_w(self, space):
        return self.bigint.toint()

    def bigint_w(self, space):
        return self.bigint

    def float_w(self, space):
        return self.bigint.tofloat()

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

    @classdef.method("<<", other="int")
    def method_left_shift(self, space, other):
        return space.newbigint_fromrbigint(self.bigint.lshift(other))

    @classdef.method("&", other="bigint")
    def method_and(self, space, other):
        return space.newbigint_fromrbigint(self.bigint.and_(other))

    @classdef.method("^", other="bigint")
    def method_xor(self, space, other):
        return space.newbigint_fromrbigint(self.bigint.xor(other))

    @classdef.method("-@")
    def method_uminus(self, space):
        return space.newbigint_fromrbigint(self.bigint.neg())

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
                "can't coerce %s to Bignum" % space.getclass(w_other).name
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
                space.newsymbol("**"),
                [w_other]
            )
        else:
            raise space.error(
                space.w_TypeError,
                "%s can't be coerced into Bignum" % space.getclass(w_other).name
            )
