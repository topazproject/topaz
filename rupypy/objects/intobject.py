from pypy.rlib import jit

from rupypy.module import ClassDef
from rupypy.objects.exceptionobject import W_ZeroDivisionError, W_TypeError
from rupypy.objects.floatobject import W_FloatObject
from rupypy.objects.integerobject import W_IntegerObject
from rupypy.objects.objectobject import W_BaseObject, MapTransitionCache
from rupypy.externalobjectstorage import ExternalObjectStorage

# This inherits from BaseObject instead of IntegerObject, because
# equal Fixnums share ivars and cannot define singleton classes
class W_FixnumObject(W_BaseObject):
    _immutable_fields_ = ["intvalue"]

    ivar_storage = ExternalObjectStorage()
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
        return self.ivar_storage.get(space, name, self.intvalue, space.w_nil)

    def set_instance_var(self, space, name, w_value):
        self.ivar_storage.set(space, name, self.intvalue, w_value)

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
