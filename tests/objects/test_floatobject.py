class TestFloatObject(object):
    def test_add(self, ec):
        w_res = ec.space.execute(ec, "return 1.0 + 2.9")
        assert ec.space.float_w(w_res) == 3.9

    def test_sub(self, ec):
        w_res = ec.space.execute(ec, "return 1.0 - 5.4")
        assert ec.space.float_w(w_res) == -4.4

    def test_mul(self, ec):
        w_res = ec.space.execute(ec, "return 1.2 * 5.0")
        assert ec.space.float_w(w_res) == 6.0

        w_res = ec.space.execute(ec, "return 1.2 * 2")
        assert ec.space.float_w(w_res) == 2.4

    def test_div(self, ec):
        w_res = ec.space.execute(ec, "return 5.0 / 2.0")
        assert ec.space.float_w(w_res) == 2.5

    def test_neg(self, ec):
        w_res = ec.space.execute(ec, "return (-5.0)")
        assert ec.space.float_w(w_res) == -5.0

        w_res = ec.space.execute(ec, "return (-(4.0 + 1.0))")
        assert ec.space.float_w(w_res) == -5.0

    def test_to_s(self, ec):
        w_res = ec.space.execute(ec, "return 1.5.to_s")
        assert ec.space.str_w(w_res) == "1.5"
