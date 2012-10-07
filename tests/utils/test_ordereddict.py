from pypy.rpython.test.test_llinterp import interpret

from rupypy.utils.ordereddict import OrderedDict


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


class TestPythonOrderedDict(BaseTestOrderedDict):
    def setup_class(cls):
        for func in cls.runner.functions:
            setattr(cls, func.__name__, staticmethod(func))


class TestRPythonOrderedDict(BaseTestOrderedDict):
    def setup_class(cls):
        def f(n, arg0):
            if arg0 == -1:
                return funcs0[n]()
            else:
                return funcs1[n](arg0)

        def make_caller(i):
            def inner(arg0=-1):
                return interpret(f, [i, arg0])
            return staticmethod(inner)

        funcs0 = []
        funcs1 = []
        for func in cls.runner.functions:
            args = func.__code__.co_argcount
            if args == 0:
                i = len(funcs0)
                funcs0.append(func)
            elif args == 1:
                i = len(funcs1)
                funcs1.append(func)
            else:
                raise NotImplementedError(args)
            setattr(cls, func.__name__, make_caller(i))
