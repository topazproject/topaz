from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object


class W_BignumObject(W_Object):
    classdef = ClassDef("Bignum", W_Object.classdef)

    def __init__(self, space, bigint):
        W_Object.__init__(self, space)
        self.bigint = bigint

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
