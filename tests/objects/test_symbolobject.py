class TestSymbolObject(object):
    def test_symbol(self, ec):
        w_res = ec.space.execute(ec, "return :foo")
        assert ec.space.symbol_w(w_res) == "foo"

    def test_to_s(self, ec):
        w_res = ec.space.execute(ec, "return :foo.to_s")
        assert ec.space.str_w(w_res) == "foo"

    def test_comparator_lt(self, ec):
        w_res = ec.space.execute(ec, "return :a <=> :b")
        assert ec.space.int_w(w_res) == -1

    def test_comparator_eq(self, ec):
        w_res = ec.space.execute(ec, "return :a <=> :a")
        assert ec.space.int_w(w_res) == 0

    def test_comparator_gt(self, ec):
        w_res = ec.space.execute(ec, "return :b <=> :a")
        assert ec.space.int_w(w_res) == 1
