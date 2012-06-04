class TestComparable(object):
    def test_gt(self, ec):
        w_res = ec.space.execute(ec, "return 'a' > 'b'")
        assert w_res is ec.space.w_false

    def test_lt(self, ec):
        w_res = ec.space.execute(ec, "return 'a' < 'b'")
        assert w_res is ec.space.w_true

    def test_ge(self, ec):
        pass

    def test_le(self, ec):
        pass

    def test_eqeq(self, ec):
        pass

    def test_between(self, ec):
        pass
