from ..base import BaseTopazTest


class TestComparable(BaseTopazTest):
    def test_name(self, space):
        space.execute("Comparable")

    def test_gt(self, space):
        w_res = space.execute("return 'a' > 'b'")
        assert self.unwrap(space, w_res) is False

    def test_lt(self, space):
        w_res = space.execute("return 'a' < 'b'")
        assert self.unwrap(space, w_res) is True

    def test_le(self, space):
        w_res = space.execute("return 'b' <= 'b'")
        assert self.unwrap(space, w_res) is True
        w_res = space.execute("return 'a' <= 'b'")
        assert self.unwrap(space, w_res) is True
        w_res = space.execute("return 'c' <= 'b'")
        assert self.unwrap(space, w_res) is False

    def test_ge(self, space):
        w_res = space.execute("return 'c' >= 'b'")
        assert self.unwrap(space, w_res) is True

    def test_eqeq(self, space):
        w_res = space.execute("return 'a' == 'a'")
        assert self.unwrap(space, w_res) is True

    def test_not_eqeq(self, space):
        w_res = space.execute("return 'a' == 'b'")
        assert self.unwrap(space, w_res) is False

    def test_between_true(self, space):
        w_res = space.execute("return 'c'.between?('b', 'd')")
        assert self.unwrap(space, w_res) is True

    def test_between_false_low(self, space):
        w_res = space.execute("return 'a'.between?('b', 'd')")
        assert self.unwrap(space, w_res) is False

    def test_between_false_high(self, space):
        w_res = space.execute("return 'e'.between?('b', 'd')")
        assert self.unwrap(space, w_res) is False

    def test_between_equal(self, space):
        w_res = space.execute("return 'e'.between?('e', 'z')")
        assert self.unwrap(space, w_res) is True
        w_res = space.execute("return 'e'.between?('a', 'e')")
        assert self.unwrap(space, w_res) is True
