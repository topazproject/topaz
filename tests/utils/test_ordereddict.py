from pypy.rpython.test.test_llinterp import interpret

from rupypy.utils.ordereddict import OrderedDict


class BaseTestOrderedDict(object):
    def test_create(self):
        def f():
            o = OrderedDict()

        self.run(f)

    def test_simple_get_set(self):
        def f():
            o = OrderedDict()
            o["a"] = 2
            return o["a"]

        assert self.run(f) == 2

    def test_custom_eq_hash(self):
        class X(object):
            def __init__(self, a):
                self.a = a

        def eq(x, y):
            return x.a == y.a

        def hash(x):
            return x.a

        def f(n):
            o = OrderedDict(eq, hash)
            o[X(n)] = 23
            return o[X(n)]
        assert self.run(f, [15]) == 23

    def test_merge_dicts(self):
        def f(n):
            if n:
                o = OrderedDict()
            else:
                o = OrderedDict()
                o[2] = "hello"
            o[3] = "goodbye"
            return o[3]


class TestPythonOrderedDict(BaseTestOrderedDict):
    def run(self, func, args=[]):
        return func(*args)


class TestRPythonOrderedDict(BaseTestOrderedDict):
    def run(self, func, args=[]):
        return interpret(func, args)
