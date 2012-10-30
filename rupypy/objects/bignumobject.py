from pypy.rlib.rbigint import rbigint

from rupypy.module import ClassDef
from rupypy.objects.integerobject import W_IntegerObject


class W_BignumObject(W_IntegerObject):
    classdef = ClassDef("Bignum", W_IntegerObject.classdef)

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

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr(self.bigint.str())

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

    @classdef.method("hash")
    def method_hash(self, space):
        return space.newint(self.bigint.hash())
