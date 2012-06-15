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


class TestPythonOrderedDict(BaseTestOrderedDict):
    def run(self, func, args=[]):
        return func(*args)


class TestRPythonOrderedDict(BaseTestOrderedDict):
    def run(self, func, args=[]):
        return interpret(func, args)
