import copy

from rpython.rlib import jit

from topaz.objects.objectobject import W_Root


class VersionTag(object):
    def __deepcopy__(self, memo):
        memo[id(self)] = result = VersionTag()
        return result


class BaseCell(W_Root):
    pass


class Cell(BaseCell):
    def __init__(self, w_value):
        self.w_value = w_value

    def __deepcopy__(self, memo):
        obj = super(Cell, self).__deepcopy__(memo)
        obj.w_value = copy.deepcopy(self.w_value, memo)
        return obj

    def getvalue(self, space, name):
        return self.w_value

    def setvalue(self, space, name, w_value):
        self.w_value = w_value


class GetterSetterCell(BaseCell):
    _immutable_fields_ = ["getter", "setter"]

    def __init__(self, getter, setter=None):
        self.getter = getter
        self.setter = setter

    def __deepcopy__(self, memo):
        obj = super(GetterSetterCell, self).__deepcopy__(memo)
        obj.getter = copy.deepcopy(self.getter, memo)
        obj.setter = copy.deepcopy(self.setter, memo)
        return obj

    def getvalue(self, space, name):
        return self.getter(space)

    def setvalue(self, space, name, w_value):
        if self.setter is None:
            raise space.error(space.w_NameError,
                              "%s is a read-only variable" % name)
        self.setter(space, w_value)


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

    def __iter__(self):
        return iter(self.values)

    def mutated(self):
        self.version = VersionTag()

    @jit.elidable
    def _get_cell(self, name, version):
        assert version is self.version
        return self.values.get(name, None)

    def get(self, space, name):
        cell = self._get_cell(name, self.version)
        if isinstance(cell, BaseCell):
            return cell.getvalue(space, name)
        else:
            return cell

    def set(self, space, name, w_value):
        cell = self._get_cell(name, self.version)
        if isinstance(cell, BaseCell):
            cell.setvalue(space, name, w_value)
        else:
            if cell is not None:
                w_value = Cell(w_value)
            self.mutated()
            self.values[name] = w_value

    def delete(self, name):
        try:
            del self.values[name]
        except KeyError:
            pass
        else:
            self.mutated()


class GlobalsDict(CellDict):
    def define_virtual(self, name, getter, setter=None):
        self.mutated()
        self.values[name] = GetterSetterCell(getter, setter)
