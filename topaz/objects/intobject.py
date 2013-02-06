import operator

from rpython.rlib.debug import check_regular_int
from rpython.rlib.rarithmetic import ovfcheck
from rpython.rlib.rbigint import rbigint
from rpython.rtyper.lltypesystem import lltype, rffi

from topaz.module import ClassDef
from topaz.objects.floatobject import W_FloatObject
from topaz.objects.integerobject import W_IntegerObject
from topaz.objects.numericobject import W_NumericObject
from topaz.objects.objectobject import W_RootObject


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

    classdef = ClassDef("Fixnum", W_IntegerObject.classdef, filepath=__file__)

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

    def new_binop(classdef, name, func):
        @classdef.method(name)
        def method(self, space, w_other):
            if space.is_kind_of(w_other, space.w_fixnum):
                other = space.int_w(w_other)
                try:
                    value = ovfcheck(func(self.intvalue, other))
                except OverflowError:
                    return space.send(
                        space.newbigint_fromint(self.intvalue), space.newsymbol(name),
                        [w_other]
                    )
                else:
                    return space.newint(value)
            elif space.is_kind_of(w_other, space.w_bignum):
                return space.send(space.newbigint_fromint(self.intvalue), space.newsymbol(name), [w_other])
            elif space.is_kind_of(w_other, space.w_float):
                return space.newfloat(func(self.intvalue, space.float_w(w_other)))
            else:
                return W_NumericObject.retry_binop_coercing(space, self, w_other, name)
        method.__name__ = "method_%s" % func.__name__
        return method
    method_add = new_binop(classdef, "+", operator.add)
    method_sub = new_binop(classdef, "-", operator.sub)
    method_mul = new_binop(classdef, "*", operator.mul)

    @classdef.method("**")
    def method_pow(self, space, w_other):
        if space.is_kind_of(w_other, space.w_fixnum):
            return self.method_pow_int_impl(space, w_other)
        elif space.getclass(w_other) is space.w_float:
            return space.send(
                space.newfloat(float(self.intvalue)), space.newsymbol("**"), [w_other]
            )
        elif space.getclass(w_other) is space.w_bignum:
            return space.send(
                space.newbigint_fromint(self.intvalue), space.newsymbol("**"),
                [w_other]
            )
        else:
            raise space.error(
                space.w_TypeError,
                "%s can't be coerced into Fixnum" % space.getclass(w_other).name
            )

    def method_pow_int_impl(self, space, w_other):
        exp = space.int_w(w_other)
        temp = self.intvalue
        if exp > 0:
            ix = 1
            try:
                while exp > 0:
                    if exp & 1:
                        ix = ovfcheck(ix * temp)
                    exp >>= 1
                    if exp == 0:
                        break
                    temp = ovfcheck(temp * temp)
            except OverflowError:
                return space.send(
                    space.newbigint_fromint(self.intvalue), space.newsymbol("**"),
                    [space.newint(exp)]
                )
            return space.newint(ix)
        else:
            return space.send(space.newfloat(float(temp)), space.newsymbol("**"), [w_other])

    @classdef.method("/", other="int")
    def method_div(self, space, other):
        try:
            return space.newint(self.intvalue / other)
        except ZeroDivisionError:
            raise space.error(space.w_ZeroDivisionError, "divided by 0")

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

    @classdef.method("|", other="int")
    def method_or(self, space, other):
        return space.newint(self.intvalue | other)

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

    def new_bool_op(classdef, name, func):
        @classdef.method(name)
        def method(self, space, w_other):
            if space.is_kind_of(w_other, space.w_float):
                return space.newbool(func(self.intvalue, space.float_w(w_other)))
            elif space.is_kind_of(w_other, space.w_fixnum):
                return space.newbool(func(self.intvalue, space.int_w(w_other)))
            else:
                return W_NumericObject.retry_binop_coercing(space, self, w_other, name, raise_error=True)
        method.__name__ = "method_%s" % func.__name__
        return method
    method_lt = new_bool_op(classdef, "<", operator.lt)
    method_lte = new_bool_op(classdef, "<=", operator.le)
    method_gt = new_bool_op(classdef, ">", operator.gt)
    method_gte = new_bool_op(classdef, ">=", operator.ge)

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

    @classdef.method("chr")
    def method_chr(self, space):
        if self.intvalue > 255 or self.intvalue < 0:
            raise space.error(space.w_RangeError, "%d out of char range" % self.intvalue)
        else:
            return space.newstr_fromstr(chr(self.intvalue))

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

    def upto(n)
        i = self
        while i <= n
            yield i
            i += 1
        end
        self
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

    def step(limit, step=1)
        idx = self
        if limit.is_a?(Float) or step.is_a?(Float)
            idx = idx.to_f
        end
        while idx <= limit do
            yield idx
            idx += step
        end
    end
    """)
