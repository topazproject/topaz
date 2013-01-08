from topaz.celldict import CellDict, Cell, GlobalsDict

from .base import BaseTopazTest


class TestCellDict(BaseTopazTest):
    def test_single_set(self, space):
        c = CellDict()
        v = c.version
        c.set(space, "a", 2)
        assert c.version is not v
        assert c._get_cell("a", c.version) == 2

    def test_multi_set(self, space):
        c = CellDict()
        c.set(space, "a", 2)
        v = c.version
        c.set(space, "a", 3)
        assert isinstance(c._get_cell("a", c.version), Cell)
        assert c.version is not v
        v = c.version
        c.set(space, "a", 4)
        assert isinstance(c._get_cell("a", c.version), Cell)
        assert c.version is v

    def test_globals(self, space):
        space.stuff = 4
        g = GlobalsDict()
        g.define_virtual("x", lambda s: s.stuff)
        assert g.get(space, "x") == 4
        with self.raises(space, "NameError"):
            g.set(space, "x", 5)

        g.define_virtual("y", lambda s: s.stuff, lambda s, v: setattr(s, "stuff", v))
        assert g.get(space, "y") == 4
        g.set(space, "y", 5)
        assert g.get(space, "y") == 5
