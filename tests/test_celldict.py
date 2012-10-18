# coding=utf-8

from rupypy.celldict import CellDict, Cell

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
