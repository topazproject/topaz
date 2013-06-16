from ..base import BaseTopazTest


class TestRangeObject(BaseTopazTest):
    def test_name(self, space):
        space.execute("Range")

    def test_map(self, space):
        w_res = space.execute("""
        return (1..3).map do |x|
          x * 5
        end
        """)
        assert self.unwrap(space, w_res) == [5, 10, 15]

    def test_float_iteration(self, space):
        w_res = space.execute("""
        return (1..3.2).map do |x|
          x
        end
        """)
        assert self.unwrap(space, w_res) == [1, 2, 3]
        w_res = space.execute("""
        return (1...3.2).map do |x|
          x
        end
        """)
        assert self.unwrap(space, w_res) == [1, 2, 3]
        with self.raises(space, "TypeError", "can't iterate from Float"):
            space.execute("(1.1..2).each { }")

    def test_starting_point_always_returned(self, space):
        w_res = space.execute("""
        return (1..1).map do |x|
          x
        end
        """)
        assert self.unwrap(space, w_res) == [1]

    def test_exclude_end(self, space):
        w_res = space.execute("return (1..5).exclude_end?")
        assert self.unwrap(space, w_res) is False

        w_res = space.execute("return (1...5).exclude_end?")
        assert self.unwrap(space, w_res) is True

    def test_eqeqeq(self, space):
        w_res = space.execute("return (1..10) === 5")
        assert w_res is space.w_true
        w_res = space.execute("return (1..10) === -1")
        assert w_res is space.w_false

    def test_begin(self, space):
        w_res = space.execute("return (1..10).begin")
        assert space.int_w(w_res) == 1

    def test_end(self, space):
        w_res = space.execute("return (1..10).end")
        assert space.int_w(w_res) == 10

    def test_range_each_chars(self, space):
        w_res = space.execute("""
        a = []
        ('a'..'e').each do |x|
          a << x
        end
        a
        """)
        assert self.unwrap(space, w_res) == ["a", "b", "c", "d", "e"]

    def test_range_each_symbols(self, space):
        w_res = space.execute("""
        a = []
        (:a..:e).each do |x|
          a << x
        end
        a
        """)
        assert self.unwrap(space, w_res) == ["a", "b", "c", "d", "e"]

    def test_each_returns_self(self, space):
        w_res = space.execute("""
        r = (1...3)
        return r.each {}.equal?(r)
        """)
        assert w_res is space.w_true
