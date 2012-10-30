from pypy.rlib.rbigint import rbigint

from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object


class W_BignumObject(W_Object):
    classdef = ClassDef("Bignum", W_Object.classdef)

    def __init__(self, space, bigint):
        W_Object.__init__(self, space)
        self.bigint = bigint

    @staticmethod
    def newbigint_fromint(space, intvalue):
        return W_BignumObject(space, rbigint.fromint(intvalue))

    @staticmethod
    def newbigint_fromrbigint(space, bigint):
        return W_BignumObject(space, bigint)

    def bigint_w(self, space):
        return self.bigint

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr(self.bigint.str())

    @classdef.method("+", other="bigint")
    def method_plus(self, space, other):
        return space.newbigint_fromrbigint(self.bigint.add(other))

    @classdef.method("-@")
    def method_uminus(self, space):
        return space.newbigint_fromrbigint(self.bigint.neg())
