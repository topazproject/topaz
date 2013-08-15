from rpython.rtyper.test.test_llinterp import interpret

from topaz.utils.ordereddict import OrderedDict


class Runner(object):
    def __init__(self):
        self.functions = []

    def func(self, f):
        self.functions.append(f)
        return f


class Simple(object):
    def __init__(self, x):
        self.x = x

    @staticmethod
    def eq(x, y):
        return x.x == y.x

    @staticmethod
    def hash(x):
        return x.x


class BaseTestOrderedDict(object):
    runner = Runner()

    @runner.func
    def create():
        OrderedDict()
        return 0

    def test_create(self):
        self.create()

    @runner.func
    def simple_get_set():
        o = OrderedDict()
        o["a"] = 2
        return o["a"]

    def test_simple_get_set(self):
        assert self.simple_get_set() == 2

    @runner.func
    def get_set_object(n):
        x = Simple(n)
        o = OrderedDict()
        o[x] = x
        return o[x].x

    def test_get_set_object(self):
        assert self.get_set_object(10) == 10

    @runner.func
    def delitem(n):
        o = OrderedDict()
        o[2] = 3
        o[3] = 4
        del o[n]
        vals = o.values()
        return vals[0] * 10 + len(vals)

    def test_delitem(self):
        assert self.delitem(2) == 41
        assert self.delitem(3) == 31

    @runner.func
    def len(n):
        o = OrderedDict()
        for i in xrange(n):
            o[i] = i
        return len(o)

    def test_len(self):
        assert self.len(2) == 2
        assert self.len(0) == 0

    @runner.func
    def custom_eq_hash(n):
        o = OrderedDict(Simple.eq, Simple.hash)
        o[Simple(n)] = 23
        return o[Simple(n)]

    def test_custom_eq_hash(self):
        assert self.custom_eq_hash(15) == 23

    @runner.func
    def merge_dicts(n):
        if n:
            o = OrderedDict()
            o[5] = 10
        else:
            o = OrderedDict()
            o[2] = 20
        o[3] = 30
        return o[3]

    def test_merge_dicts(self):
        assert self.merge_dicts(1) == 30

    @runner.func
    def grow(n):
        o = OrderedDict()
        for i in xrange(n):
            o[i] = -20
        return o[3]

    def test_grow(self):
        assert self.grow(10) == -20

    @runner.func
    def keys(n):
        o = OrderedDict()
        o[4] = 1
        o[5] = 2
        o[4] = 2
        return o.keys()[n]

    def test_keys(self):
        assert self.keys(0) == 4
        assert self.keys(1) == 5

    @runner.func
    def values(n):
        o = OrderedDict()
        o[4] = 1
        o[5] = 2
        o[4] = 3
        return o.values()[n]

    def test_values(self):
        assert self.values(0) == 3
        assert self.values(1) == 2

    @runner.func
    def keys_object(n):
        o = OrderedDict()
        o[Simple(1)] = None
        o[Simple(2)] = None
        o[Simple(3)] = None
        return o.keys()[n].x

    def test_keys_object(self):
        assert self.keys_object(2) == 3

    @runner.func
    def get(n):
        o = OrderedDict()
        o[4] = 3
        return o.get(n, 123)

    def test_get(self):
        assert self.get(12) == 123
        assert self.get(4) == 3

    @runner.func
    def iteritems(n):
        o = OrderedDict()
        o[0] = 10
        o[2] = 15
        o[3] = 12
        r = []
        for k, v in o.iteritems():
            r.append((k, v))
        p = r[n]
        return p[0] * 100 + p[1]

    def test_iteritems(self):
        assert self.iteritems(0) == 10
        assert self.iteritems(2) == 312
        assert self.iteritems(1) == 215

    @runner.func
    def iteritems_next_method(n):
        o = OrderedDict()
        o[n] = 5
        it = o.iteritems()
        return it.next()[1]

    def test_iteritems_next_method(self):
        assert self.iteritems_next_method(2) == 5

    @runner.func
    def contains(n):
        o = OrderedDict()
        o[4] = 5
        return n in o

    def test_contains(self):
        assert self.contains(4)
        assert not self.contains(5)

    @runner.func
    def pop(n):
        o = OrderedDict()
        o[1] = 12
        o[2] = 3
        return (o.pop(n) * 10) + len(o)

    def test_pop(self):
        assert self.pop(1) == 121
        assert self.pop(2) == 31

    @runner.func
    def pop_default(n, d):
        o = OrderedDict()
        o[1] = 12
        o[2] = 3
        return (o.pop(n, d) * 10) + len(o)

    def test_pop_default(self):
        assert self.pop_default(10, 14) == 142

    @runner.func
    def pop_keyerror(n):
        o = OrderedDict()
        o[3] = 4
        try:
            return o.pop(n)
        except KeyError:
            return 500

    def test_pop_keyerror(self):
        assert self.pop_keyerror(3) == 4
        assert self.pop_keyerror(12) == 500

    @runner.func
    def update(n):
        o = OrderedDict()
        o[3] = 4
        v = OrderedDict()
        v[n] = 5
        o.update(v)
        return o[3]

    def test_update(self):
        assert self.update(3) == 5
        assert self.update(22) == 4

    @runner.func
    def clear():
        o = OrderedDict()
        o[3] = 4
        o.clear()
        return len(o)

    def test_clear(self):
        assert self.clear() == 0

    @runner.func
    def truthy(n):
        o = OrderedDict()
        if n:
            o[n] = n
        return bool(o)

    def test_truthiness(self):
        assert self.truthy(3)
        assert not self.truthy(0)

    @runner.func
    def popitem(n):
        o = OrderedDict()
        if n:
            o[n] = n
        try:
            key, val = o.popitem()
        except KeyError:
            return 400
        else:
            return key * 10 + val

    def test_popitem(self):
        assert self.popitem(0) == 400
        assert self.popitem(4) == 44

    @runner.func
    def copy(n):
        o = OrderedDict(Simple.eq, Simple.hash)
        o[Simple(n)] = n
        d = o.copy()
        return d.values()[0] * 10 + len(d)

    def test_copy(self):
        assert self.copy(3) == 31


class TestPythonOrderedDict(BaseTestOrderedDict):
    def setup_class(cls):
        for func in cls.runner.functions:
            setattr(cls, func.__name__, staticmethod(func))


class TestRPythonOrderedDict(BaseTestOrderedDict):
    def setup_class(cls):
        def f(n, arg0, arg1):
            if arg0 == -1:
                return funcs0[n]()
            else:
                if arg1 == -1:
                    return funcs1[n](arg0)
                else:
                    return funcs2[n](arg0, arg1)

        def make_caller(i):
            def inner(arg0=-1, arg1=-1):
                return interpret(f, [i, arg0, arg1])
            return staticmethod(inner)

        funcs0 = []
        funcs1 = []
        funcs2 = []
        for func in cls.runner.functions:
            args = func.__code__.co_argcount
            if args == 0:
                i = len(funcs0)
                funcs0.append(func)
            elif args == 1:
                i = len(funcs1)
                funcs1.append(func)
            elif args == 2:
                i = len(funcs2)
                funcs2.append(func)
            else:
                raise NotImplementedError(args)
            setattr(cls, func.__name__, make_caller(i))
