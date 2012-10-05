import copy

from pypy.rlib import jit

from rupypy.objects.objectobject import W_BaseObject


class VersionTag(object):
    def __deepcopy__(self, memo):
        memo[id(self)] = result = VersionTag()
        return result


class Cell(W_BaseObject):
    def __init__(self, name):
        self.name = name
        self.w_value = None

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
        return self.values.setdefault(name, Cell(name))
