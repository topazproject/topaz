class TestComparable(object):
    def test_name(self, space):
        space.execute("Comparable")

    def test_gt(self, space):
        w_res = space.execute("return 'a' > 'b'")
        assert w_res is space.w_false

    def test_lt(self, space):
        w_res = space.execute("return 'a' < 'b'")
        assert w_res is space.w_true

    def test_le(self, space):
        w_res = space.execute("return 'b' <= 'b'")
        assert w_res is space.w_true
        w_res = space.execute("return 'a' <= 'b'")
        assert w_res is space.w_true
        w_res = space.execute("return 'c' <= 'b'")
        assert w_res is space.w_false

    def test_ge(self, space):
        w_res = space.execute("return 'c' >= 'b'")
        assert w_res is space.w_true

    def test_eqeq(self, space):
        w_res = space.execute("return 'a' == 'a'")
        assert w_res is space.w_true

    def test_not_eqeq(self, space):
        w_res = space.execute("return 'a' == 'b'")
        assert w_res is space.w_false

    def test_between_true(self, space):
        w_res = space.execute("return 'c'.between?('b', 'd')")
        assert w_res is space.w_true

    def test_between_false_low(self, space):
        w_res = space.execute("return 'a'.between?('b', 'd')")
        assert w_res is space.w_false

    def test_between_false_high(self, space):
        w_res = space.execute("return 'e'.between?('b', 'd')")
        assert w_res is space.w_false

    def test_between_equal(self, space):
        w_res = space.execute("return 'e'.between?('e', 'z')")
        assert w_res is space.w_true
        w_res = space.execute("return 'e'.between?('a', 'e')")
        assert w_res is space.w_true
