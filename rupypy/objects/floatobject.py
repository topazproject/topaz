from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_BaseObject


class W_FloatObject(W_BaseObject):
    classdef = ClassDef("Float", W_BaseObject.classdef)

    def __init__(self, floatvalue):
        self.floatvalue = floatvalue

    def float_w(self, space):
        return self.floatvalue

    @classdef.method("to_f")
    def method_to_f(self, space):
        return self

    @classdef.method("*")
    def method_mul(self, space, w_other):
        return space.newfloat(self.floatvalue * space.float_w(w_other))