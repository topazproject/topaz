class TestSymbolObject(object):
    def test_symbol(self, ec):
        w_res = ec.space.execute(ec, "return :foo")
        assert ec.space.symbol_w(w_res) == "foo"

    def test_to_s(self, ec):
        w_res = ec.space.execute(ec, "return :foo.to_s")
        assert ec.space.str_w(w_res) == "foo"
    
    #def test_object_id(self, ec):
    #    w_res = ec.space.execute(ec, "return :foo.object_id")
    #    print ec.space.int_w(w_res)
    #    assert ec.space.int_w(w_res) > 0