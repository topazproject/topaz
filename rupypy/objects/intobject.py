from pypy.rlib.debug import check_regular_int
from pypy.rlib.rarithmetic import ovfcheck
from pypy.rlib.rbigint import rbigint
from pypy.rpython.lltypesystem import lltype, rffi

from rupypy.module import ClassDef
from rupypy.objects.floatobject import W_FloatObject
from rupypy.objects.integerobject import W_IntegerObject
from rupypy.objects.numericobject import W_NumericObject
from rupypy.objects.objectobject import W_RootObject


class FixnumStorage(object):
    def __init__(self, space):
        self.storages = {}

    def get_or_create(self, space, intvalue):
        try:
            storage = self.storages[intvalue]
        except KeyError:
            self.storages[intvalue] = storage = space.send(space.w_object, space.newsymbol("new"))
        return storage


class W_FixnumObject(W_RootObject):
    _immutable_fields_ = ["intvalue"]

    classdef = ClassDef("Fixnum", W_IntegerObject.classdef)

    def __init__(self, space, intvalue):
        check_regular_int(intvalue)
        self.intvalue = intvalue

    def __deepcopy__(self, memo):
        obj = super(W_FixnumObject, self).__deepcopy__(memo)
        obj.intvalue = self.intvalue
        return obj

    def int_w(self, space):
        return self.intvalue

    def bigint_w(self, space):
        return rbigint.fromint(self.intvalue)

    def float_w(self, space):
        return float(self.intvalue)

    def getsingletonclass(self, space):
        raise space.error(space.w_TypeError, "can't define singleton")

    def find_instance_var(self, space, name):
        storage = space.fromcache(FixnumStorage).get_or_create(space, self.intvalue)
        return storage.find_instance_var(space, name)

    def set_instance_var(self, space, name, w_value):
        storage = space.fromcache(FixnumStorage).get_or_create(space, self.intvalue)
        storage.set_instance_var(space, name, w_value)

    @classdef.method("inspect")
    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr(str(self.intvalue))

    @classdef.method("to_f")
    def method_to_f(self, space):
        return space.newfloat(float(self.intvalue))

    @classdef.method("to_i")
    @classdef.method("to_int")
    def method_to_i(self, space):
        return self

    @classdef.method("+")
    def method_add(self, space, w_other):
        if isinstance(w_other, W_FloatObject):
            return space.newfloat(self.intvalue + space.float_w(w_other))
        else:
            other = space.int_w(w_other)
            try:
                value = ovfcheck(self.intvalue + other)
            except OverflowError:
                return space.send(
                    space.newbigint_fromint(self.intvalue), space.newsymbol("+"),
                    [w_other]
                )
            else:
                return space.newint(value)

    @classdef.method("-")
    def method_sub(self, space, w_other):
        if isinstance(w_other, W_FloatObject):
            return space.newfloat(self.intvalue - space.float_w(w_other))
        else:
            other = space.int_w(w_other)
            try:
                value = ovfcheck(self.intvalue - other)
            except OverflowError:
                return space.send(
                    space.newbigint_fromint(self.intvalue), space.newsymbol("-"),
                    [w_other]
                )
            else:
                return space.newint(value)

    @classdef.method("*", other="int")
    def method_mul(self, space, other):
        try:
            value = ovfcheck(self.intvalue * other)
        except OverflowError:
            return space.send(
                space.newbigint_fromint(self.intvalue), space.newsymbol("*"),
                [space.newint(other)]
            )
        else:
            return space.newint(value)

    @classdef.method("/", other="int")
    def method_div(self, space, other):
        try:
            return space.newint(self.intvalue / other)
        except ZeroDivisionError:
            raise space.error(space.w_ZeroDivisionError,
                "divided by 0"
            )

    @classdef.method("%", other="int")
    def method_mod(self, space, other):
        return space.newint(self.intvalue % other)

    @classdef.method("<<", other="int")
    def method_left_shift(self, space, other):
        if other < 0:
            return space.newint(self.intvalue >> -other)
        else:
            try:
                value = ovfcheck(self.intvalue << other)
            except OverflowError:
                return space.send(
                    space.newbigint_fromint(self.intvalue), space.newsymbol("<<"),
                    [space.newint(other)]
                )
            else:
                return space.newint(value)

    @classdef.method("&", other="int")
    def method_and(self, space, other):
        return space.newint(self.intvalue & other)

    @classdef.method("^", other="int")
    def method_xor(self, space, other):
        return space.newint(self.intvalue ^ other)

    @classdef.method("==")
    def method_eq(self, space, w_other):
        if isinstance(w_other, W_FixnumObject):
            return space.newbool(self.comparator(space, space.int_w(w_other)) == 0)
        elif isinstance(w_other, W_FloatObject):
            return space.newbool(self.comparator(space, space.float_w(w_other)) == 0)
        else:
            return space.send(w_other, space.newsymbol("=="), [self])

    @classdef.method("!=")
    def method_ne(self, space, w_other):
        return space.newbool(space.send(self, space.newsymbol("=="), [w_other]) is space.w_false)

    @classdef.method("<", other="int")
    def method_lt(self, space, other):
        return space.newbool(self.intvalue < other)

    @classdef.method(">", other="int")
    def method_gt(self, space, other):
        return space.newbool(self.intvalue > other)

    @classdef.method("<=")
    def method_lte(self, space, w_other):
        if isinstance(w_other, W_FloatObject):
            return space.newbool(self.intvalue <= space.float_w(w_other))
        elif isinstance(w_other, W_FixnumObject):
            return space.newbool(self.intvalue <= w_other.intvalue)
        else:
            return W_NumericObject.retry_binop_coercing(space, self, w_other, "<=", raise_error=True)

    @classdef.method(">=", other="int")
    def method_gte(self, space, other):
        return space.newbool(self.intvalue >= other)

    @classdef.method("-@")
    def method_neg(self, space):
        return space.newint(-self.intvalue)

    @classdef.method("<=>")
    def method_comparator(self, space, w_other):
        if isinstance(w_other, W_FixnumObject):
            return space.newint(self.comparator(space, space.int_w(w_other)))
        elif isinstance(w_other, W_FloatObject):
            return space.newint(self.comparator(space, space.float_w(w_other)))
        else:
            return space.w_nil

    def comparator(self, space, other):
        if self.intvalue < other:
            return -1
        elif self.intvalue == other:
            return 0
        elif self.intvalue > other:
            return 1
        return 1

    @classdef.method("hash")
    def method_hash(self, space):
        return self

    @classdef.method("size")
    def method_size(self, space):
        return space.newint(rffi.sizeof(lltype.typeOf(self.intvalue)))

    @classdef.method("coerce")
    def method_coerce(self, space, w_other):
        if space.getclass(w_other) is space.getclass(self):
            return space.newarray([w_other, self])
        else:
            return space.newarray([space.send(self, space.newsymbol("Float"), [w_other]), self])

    classdef.app_method("""
    def next
        succ
    end

    def succ
        self + 1
    end

    def times
        i = 0
        while i < self
            yield i
            i += 1
        end
    end

    def zero?
        self == 0
    end

    def nonzero?
        self != 0
    end

    def even?
        self % 2 == 0
    end

    def odd?
        self % 2 != 0
    end

    def __id__
        self * 2 + 1
    end
    """)
