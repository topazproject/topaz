class TestSymbolObject(object):
    def test_symbol(self, ec):
        w_res = ec.space.execute(ec, "return :foo")
        assert ec.space.symbol_w(w_res) == "foo"

    def test_to_s(self, ec):
        w_res = ec.space.execute(ec, "return :foo.to_s")
        assert ec.space.str_w(w_res) == "foo"
