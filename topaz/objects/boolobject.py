from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object


class W_BoolObject(W_Object):
    _attrs_ = ["boolvalue"]
    _immutable_fields_ = ["boolvalue"]

    def __init__(self, space, boolvalue):
        W_Object.__init__(self, space)
        self.boolvalue = boolvalue

    def __deepcopy__(self, memo):
        obj = super(W_BoolObject, self).__deepcopy__(memo)
        obj.boolvalue = self.boolvalue
        return obj

    def is_true(self, space):
        return self.boolvalue

    def getclass(self, space):
        if self.boolvalue:
            return space.getclassobject(true_classdef)
        else:
            return space.getclassobject(false_classdef)

    def getsingletonclass(self, space):
        return self.getclass(space)


true_classdef = ClassDef("TrueClass", W_Object.classdef)
true_classdef.cls = W_BoolObject

false_classdef = ClassDef("FalseClass", W_Object.classdef)
false_classdef.cls = W_BoolObject


@true_classdef.method("inspect")
@true_classdef.method("to_s")
def true_method_to_s(self, space):
    return space.newstr_fromstr("true")


@false_classdef.method("inspect")
@false_classdef.method("to_s")
def false_method_to_s(self, space):
    return space.newstr_fromstr("false")


@true_classdef.method("==")
def true_method_eq(self, space, w_other):
    return space.newbool(
        isinstance(w_other, W_BoolObject) and self.boolvalue == w_other.boolvalue
    )


@false_classdef.method("==")
def false_method_eq(self, space, w_other):
    return space.newbool(
        isinstance(w_other, W_BoolObject) and self.boolvalue == w_other.boolvalue
    )


@true_classdef.method("&")
def true_methof_and(self, space, w_other):
    return space.newbool(space.is_true(w_other))


@false_classdef.method("&")
def false_methof_and(self, space, w_other):
    return space.w_false


@true_classdef.method("|")
def true_method_or(self, space, w_other):
    return space.w_true


@false_classdef.method("|")
def false_method_or(self, space, w_other):
    return space.newbool(space.is_true(w_other))


@true_classdef.method("^")
def true_method_xor(self, space, w_other):
    return space.newbool(not space.is_true(w_other))


@false_classdef.method("^")
def false_method_xor(self, space, w_other):
    return space.newbool(space.is_true(w_other))
