from ..base import BaseRuPyPyTest


class TestSymbolObject(BaseRuPyPyTest):
    def test_name(self, space):
        space.execute("Symbol")

    def test_symbol(self, space):
        w_res = space.execute("return :foo")
        assert space.symbol_w(w_res) == "foo"

    def test_to_s(self, space):
        w_res = space.execute("return :foo.to_s")
        assert space.str_w(w_res) == "foo"

    def test_inspect(self, space):
        w_res = space.execute("return :foo.inspect")
        assert space.str_w(w_res) == ":foo"

    def test_comparator_lt(self, space):
        w_res = space.execute("return :a <=> :b")
        assert space.int_w(w_res) == -1

    def test_comparator_eq(self, space):
        w_res = space.execute("return :a <=> :a")
        assert space.int_w(w_res) == 0

    def test_comparator_gt(self, space):
        w_res = space.execute("return :b <=> :a")
        assert space.int_w(w_res) == 1

    def test_comparator_non_symbol(self, space):
        w_res = space.execute("return :a <=> 12")
        assert w_res is space.w_nil

    def test_identity(self, space):
        w_res = space.execute("return [:x.object_id, :x.object_id]")
        id1, id2 = self.unwrap(space, w_res)
        assert id1 == id2

    def test_to_sym(self, space):
        w_res = space.execute("return :x, :x.to_sym")
        s1, s2 = self.unwrap(space, w_res)
        assert s1 == s2 == "x"
