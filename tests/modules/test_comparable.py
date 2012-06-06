class TestComparable(object):
    def test_gt(self, ec):
        w_res = ec.space.execute(ec, "return 'a' > 'b'")
        assert w_res is ec.space.w_false

    def test_lt(self, ec):
        w_res = ec.space.execute(ec, "return 'a' < 'b'")
        assert w_res is ec.space.w_true

    def test_ge(self, ec):
        w_res = ec.space.execute(ec, "return 'b' <= 'b'")
        assert w_res is ec.space.w_true

    def test_le(self, ec):
        w_res = ec.space.execute(ec, "return 'c' >= 'b'")
        assert w_res is ec.space.w_true

    def test_eqeq(self, ec):
        w_res = ec.space.execute(ec, "return 'a' == 'a'")
        assert w_res is ec.space.w_true

    def test_not_eqeq(self, ec):
        w_res = ec.space.execute(ec, "return 'a' == 'b'")
        assert w_res is ec.space.w_false

    def test_between_true(self, ec):
        w_res = ec.space.execute(ec, "return 'c'.between?('b', 'd')")
        assert w_res is ec.space.w_true

    def test_between_false_low(self, ec):
        w_res = ec.space.execute(ec, "return 'a'.between?('b', 'd')")
        assert w_res is ec.space.w_false

    def test_between_false_high(self, ec):
        w_res = ec.space.execute(ec, "return 'e'.between?('b', 'd')")
        assert w_res is ec.space.w_false
