import copy

from pypy.rlib import jit

from rupypy.objects.objectobject import W_BaseObject


class VersionTag(object):
    def __deepcopy__(self, memo):
        memo[id(self)] = result = VersionTag()
        return result


class Cell(W_BaseObject):
    def __init__(self, name, w_value=None):
        self.name = name
        self.w_value = w_value

    def __deepcopy__(self, memo):
        obj = super(Cell, self).__deepcopy__(memo)
        obj.name = self.name
        obj.w_value = copy.deepcopy(self.w_value, memo)
        return obj


class CellDict(object):
    _immutable_fields_ = ["version?"]

    def __init__(self):
        self.values = {}
        self.version = VersionTag()

    def __deepcopy__(self, memo):
        c = object.__new__(self.__class__)
        c.values = copy.deepcopy(self.values, memo)
        c.version = copy.deepcopy(self.version, memo)
        return c

    def mutated(self):
        self.version = VersionTag()

    def get(self, name):
        cell = self._get_cell(name, self.version)
        if isinstance(cell, Cell):
            return cell.w_value
        else:
            return cell

    def set(self, name, w_value):
        cell = self._get_cell(name, self.version)
        if isinstance(cell, Cell):
            cell.w_value = w_value
        else:
            if cell is not None:
                w_value = Cell(name, w_value)
            self.mutated()
            self.values[name] = w_value

    def delete(self, name):
        try:
            del self.values[name]
        except KeyError:
            pass
        else:
            self.mutated()

    @jit.elidable
    def _get_cell(self, name, version):
        assert version is self.version
        return self.values.get(name, None)
