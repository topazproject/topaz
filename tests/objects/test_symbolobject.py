from ..base import BaseRuPyPyTest


class TestSymbolObject(BaseRuPyPyTest):
    def test_symbol(self, space):
        w_res = space.execute("return :foo")
        assert space.symbol_w(w_res) == "foo"

    def test_to_s(self, space):
        w_res = space.execute("return :foo.to_s")
        assert space.str_w(w_res) == "foo"

    def test_comparator_lt(self, space):
        w_res = space.execute("return :a <=> :b")
        assert space.int_w(w_res) == -1

    def test_comparator_eq(self, space):
        w_res = space.execute("return :a <=> :a")
        assert space.int_w(w_res) == 0

    def test_comparator_gt(self, space):
        w_res = space.execute("return :b <=> :a")
        assert space.int_w(w_res) == 1

    def test_identity(self, space):
        w_res = space.execute("return [:x.object_id, :x.object_id]")
        id1, id2 = self.unwrap(space, w_res)
        assert id1 == id2

    def test_subscript(self, space):
        w_res = space.execute("return :abc[1]")
        assert space.str_w(w_res) == "b"

    def test_length(self, space):
        w_res = space.execute("return :abc.length")
        assert space.int_w(w_res) == 3

    def test_class_function(self, space):
        w_res = space.execute("return Symbol.all_symbols")
        symbols = self.unwrap(space, w_res)
        length = len(symbols)
        assert length > 0
        
        w_res = space.execute("return :abc.class.all_symbols")
        symbols = self.unwrap(space, w_res)
        assert length < len(symbols)
        assert symbols.count('abc') == 1

    def test_object_id(self, space):
        w_res = space.execute("return :abc.object_id")
        assert space.int_w(w_res) > 0
