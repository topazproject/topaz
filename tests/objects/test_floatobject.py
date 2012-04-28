class TestFloatObject(object):
    def test_add(self, space):
        w_res = space.execute("return 1.0 + 2.9")
        assert space.float_w(w_res) == 3.9

    def test_mul(self, space):
        w_res = space.execute("return 1.2 * 5.0")
        assert space.float_w(w_res) == 6.0

        w_res = space.execute("return 1.2 * 2")
        assert space.float_w(w_res) == 2.4