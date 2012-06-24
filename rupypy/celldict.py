from pypy.rlib import jit

from rupypy.objects.objectobject import W_BaseObject


class VersionTag(object):
    pass


class Cell(W_BaseObject):
    def __init__(self, name):
        self.name = name
        self.w_value = None


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
