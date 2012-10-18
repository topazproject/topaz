from rupypy.celldict import CellDict, Cell, GlobalsDict

from .base import BaseRuPyPyTest


class TestCellDict(BaseRuPyPyTest):
    def test_single_set(self):
        c = CellDict()
        v = c.version
        c.set("a", 2)
        assert c.version is not v
        assert c._get_cell("a", c.version) == 2

    def test_multi_set(self):
        c = CellDict()
        c.set("a", 2)
        v = c.version
        c.set("a", 3)
        assert isinstance(c._get_cell("a", c.version), Cell)
        assert c.version is not v
        v = c.version
        c.set("a", 4)
        assert isinstance(c._get_cell("a", c.version), Cell)
        assert c.version is v

    def test_globals(self, space):
        space.stuff = 4
        g = GlobalsDict(space)
        g.def_virtual('x', lambda s: s.stuff)
        assert g.get('x') == 4
        with self.raises(space, "NameError"):
            g.set('x', 5)

        g.def_virtual('y', lambda s: s.stuff, lambda s, v: setattr(s, 'stuff', v))
        assert g.get('y') == 4
        g.set('y', 5)
        assert g.get('y') == 5
