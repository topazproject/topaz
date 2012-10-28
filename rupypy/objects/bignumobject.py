from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object


class W_BignumObject(W_Object):
    classdef = ClassDef("Bignum", W_Object.classdef)

    def __init__(self, space, bigint):
        W_Object.__init__(self, space)
        self.bigint = bigint

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr(self.bigint.str())
