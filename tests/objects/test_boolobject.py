class TestTrueObject(object):
    def test_to_s(self, ec):
        w_res = ec.space.execute(ec, "return true.to_s")
        assert ec.space.str_w(w_res) == "true"


class TestFalseObject(object):
    def test_to_s(self, ec):
        w_res = ec.space.execute(ec, "return false.to_s")
        assert ec.space.str_w(w_res) == "false"
