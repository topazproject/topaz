# coding=utf-8

from rupypy.celldict import CellDict, Cell, GlobalsDict

from .base import BaseRuPyPyTest


class TestCellDict(BaseRuPyPyTest):
    def test_cell_optimization(self):
        d = CellDict()
        d.set(1, 3)
        assert d.values[1] == 3

        d.set(1, 4)
        v = d.values[1]
        assert type(v) == Cell
        assert v.w_value == 4

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
