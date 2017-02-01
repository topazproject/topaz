import os
import time

from rpython.rlib.rarithmetic import intmask
from rpython.rlib.rrandom import Random

from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object
from topaz.objects.rangeobject import W_RangeObject
from topaz.objects.bignumobject import W_BignumObject
from topaz.coerce import Coerce


class W_RandomObject(W_Object):
    classdef = ClassDef("Random", W_Object.classdef)

    def __init__(self, space, seed=0, klass=None):
        W_Object.__init__(self, space, klass)
        self.w_seed = None
        self.random = Random(abs(seed))

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        default = space.send(w_cls, "new")
        space.set_const(w_cls, "DEFAULT", default)

    @classdef.singleton_method("allocate")
    def method_allocate(self, space):
        return W_RandomObject(space, 0, self)

    @classdef.method("initialize")
    def method_initialize(self, space, w_seed=None):
        self.srand(space, w_seed)

    @classdef.method("seed")
    def method_seed(self, space):
        return self.w_seed

    def srand(self, space, seed=None):
        previous_seed = self.w_seed
        if seed is None:
            seed = intmask(self._generate_seed())
        else:
            seed = Coerce.int(space, seed)
        self.w_seed = space.newint(seed)
        if previous_seed is None:
            value = space.newfloat(self.random.random())
        else:
            value = previous_seed
        self.random = Random(abs(seed))
        return value

    @classdef.method("rand")
    def method_rand(self, space, w_max=None):
        if w_max is None:
            return space.newfloat(self.random.random())
        elif space.is_kind_of(w_max, space.w_float):
            return self._rand_float(space, w_max)
        elif space.is_kind_of(w_max, space.getclassfor(W_BignumObject)):
            return self._rand_bignum(space, w_max)
        elif space.is_kind_of(w_max, space.getclassfor(W_RangeObject)):
            return self._rand_range(space, w_max)
        else:
            return self._rand_int(space, w_max)

    @classdef.singleton_method("rand")
    def method_singleton_rand(self, space, args_w):
        default = space.find_const(self, "DEFAULT")
        return space.send(default, "rand", args_w)

    def _rand_range(self, space, range):
        random = self.random.random()
        first = space.send(range, "first")
        last = space.send(range, "last")
        if space.is_true(space.send(range, "include?", [last])):
            last = space.send(last, "+", [space.newint(1)])
        if (not space.respond_to(last, "-") or
            not space.respond_to(last, "+")):
                raise space.error(space.w_ArgumentError, "invalid argument")
        diff = space.send(last, "-", [first])
        offset = space.send(diff, "*", [space.newfloat(random)])
        choice = space.send(offset, "+", [first])
        if (not space.is_kind_of(first, space.w_float) and
            not space.is_kind_of(last, space.w_float)):
            choice = space.send(choice, "to_i")
        return choice

    def _rand_float(self, space, float):
        random = self.random.random()
        max = Coerce.float(space, float)
        if max <= 0:
            raise space.error(space.w_ArgumentError, "invalid argument")
        return space.newfloat(random * max)

    def _rand_int(self, space, integer):
        random = self.random.random()
        max = Coerce.int(space, integer)
        if max <= 0:
            raise space.error(space.w_ArgumentError, "invalid argument")
        else:
            return space.newint(int(random * max))

    def _rand_bignum(self, space, bignum):
        random = self.random.random()
        max = Coerce.float(space, bignum)
        if max <= 0:
            raise space.error(space.w_ArgumentError, "invalid argument")
        return space.newbigint_fromfloat(random * max)

    def _generate_seed(self):
        seed = 0
        if os.access('/dev/urandom', os.R_OK):
            file = os.open('/dev/urandom', os.R_OK, 0644)
            bytes = os.read(file, 4)
            os.close(file)
            for b in bytes:
                seed = seed * 0xff + ord(b)
        return seed + int(time.time()) + os.getpid()
