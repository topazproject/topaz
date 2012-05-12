class TestNilObject(object):
    def test_to_s(self, ec):
        w_res = ec.space.execute(ec, "return nil.to_s")
        assert ec.space.str_w(w_res) == ""
