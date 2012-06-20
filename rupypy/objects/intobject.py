from pypy.rlib import jit

from rupypy.module import ClassDef
from rupypy.objects.exceptionobject import W_ZeroDivisionError, W_TypeError
from rupypy.objects.floatobject import W_FloatObject
from rupypy.objects.integerobject import W_IntegerObject
from rupypy.objects.objectobject import W_BaseObject, MapTransitionCache

# This inherits from BaseObject instead of IntegerObject, because
# equal Fixnums share ivars and cannot define singleton classes
class W_FixnumObject(W_BaseObject):
    ivar_storage = {}
    ivar_list = []

    _immutable_fields_ = ["intvalue"]

    classdef = ClassDef("Fixnum", W_IntegerObject.classdef)

    def __init__(self, space, intvalue):
        self.intvalue = intvalue

    def int_w(self, space):
        return self.intvalue

    def float_w(self, space):
        return float(self.intvalue)

    def getsingletonclass(self, space):
        space.raise_(space.getclassfor(W_TypeError), "can't define singleton")

    def find_instance_var(self, space, name):
        if name not in W_FixnumObject.ivar_list:
            return space.w_nil
        ary = W_FixnumObject.ivar_storage.get(self.intvalue, None)
        if ary is not None:
            return ary[W_FixnumObject.ivar_list.index(name)]
        else:
            return space.w_nil

    def set_instance_var(self, space, name, w_value):
        if name not in W_FixnumObject.ivar_list:
            idx = len(W_FixnumObject.ivar_list)
            W_FixnumObject.ivar_list.append(name)
        else:
            idx = W_FixnumObject.ivar_list.index(name)
        ary = W_FixnumObject.ivar_storage.setdefault(self.intvalue, {})
        ary[idx] = w_value

    @classdef.method("__id__")
    @classdef.method("object_id")
    def method___id__(self, space):
        return self

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr(str(self.intvalue))

    @classdef.method("to_f")
    def method_to_f(self, space):
        return space.newfloat(float(self.intvalue))

    @classdef.method("+")
    def method_add(self, space, w_other):
        if isinstance(w_other, W_FloatObject):
            return space.newfloat(self.intvalue + space.float_w(w_other))
        else:
            return space.newint(self.intvalue + space.int_w(w_other))

    @classdef.method("-")
    def method_sub(self, space, w_other):
        if isinstance(w_other, W_FloatObject):
            return space.newfloat(self.intvalue - space.float_w(w_other))
        else:
            return space.newint(self.intvalue - space.int_w(w_other))

    @classdef.method("*", other="int")
    def method_mul(self, space, other):
        return space.newint(self.intvalue * other)

    @classdef.method("/", other="int")
    def method_div(self, space, other):
        try:
            return space.newint(self.intvalue / 0)
        except ZeroDivisionError:
            raise space.raise_(space.getclassfor(W_ZeroDivisionError),
                "divided by 0"
            )

    @classdef.method("===", other="int")
    @classdef.method("==", other="int")
    def method_eq(self, space, other):
        return space.newbool(self.intvalue == other)

    @classdef.method("!=", other="int")
    def method_ne(self, space, other):
        return space.newbool(self.intvalue != other)

    @classdef.method("<", other="int")
    def method_lt(self, space, other):
        return space.newbool(self.intvalue < other)

    @classdef.method(">", other="int")
    def method_gt(self, space, other):
        return space.newbool(self.intvalue > other)

    @classdef.method("-@")
    def method_neg(self, space):
        return space.newint(-self.intvalue)

    @classdef.method("<=>", other="int")
    def method_comparator(self, space, other):
        if self.intvalue < other:
            return space.newint(-1)
        elif self.intvalue == other:
            return space.newint(0)
        elif self.intvalue > other:
            return space.newint(1)

    @classdef.method("hash")
    def method_hash(self, space):
        return self

    classdef.app_method("""
    def times
        i = 0
        while i < self
            yield i
            i += 1
        end
    end
    """)
