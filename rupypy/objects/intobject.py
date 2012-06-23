from rupypy.module import ClassDef
from rupypy.objects.exceptionobject import W_ZeroDivisionError, W_TypeError
from rupypy.objects.floatobject import W_FloatObject
from rupypy.objects.integerobject import W_IntegerObject
from rupypy.objects.objectobject import W_RootObject, W_Object


class FixnumStorage(object):
    def __init__(self, space):
        self.storages = {}

    def get_or_create(self, space, intvalue):
        try:
            storage = self.storages[intvalue]
        except KeyError:
            self.storages[intvalue] = storage = space.send(space.getclassfor(W_Object), space.newsymbol("new"))
        return storage


class W_FixnumObject(W_RootObject):
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
        storage = space.fromcache(FixnumStorage).get_or_create(space, self.intvalue)
        return storage.find_instance_var(space, name)

    def set_instance_var(self, space, name, w_value):
        storage = space.fromcache(FixnumStorage).get_or_create(space, self.intvalue)
        storage.set_instance_var(space, name, w_value)

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

    classdef.app_method("""
    def __id__
        self * 2 + 1
    end
    """)
