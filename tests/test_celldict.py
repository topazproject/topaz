from rupypy.celldict import CellDict, Cell


class TestCellDict(object):
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
