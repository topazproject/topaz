from pypy.rlib import jit


class GlobalValue(object):
    def __init__(self, space, name):
        self.name = name
        self.w_value = space.w_nil


class Globals(object):
    def __init__(self):
        self.values = {}

    def get(self, space, name):
        return self._get_cell(space, name).w_value

    def set(self, space, name, w_value):
        self._get_cell(space, name).w_value = w_value

    @jit.elidable
    def _get_cell(self, space, name):
        return self.values.setdefault(name, GlobalValue(space, name))
