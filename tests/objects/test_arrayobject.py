from ..base import BaseRuPyPyTest


class TestArrayObject(BaseRuPyPyTest):
    def test_to_s(self, space):
        w_res = space.execute("return [].to_s")
        assert space.str_w(w_res) == "[]"

        w_res = space.execute("return [[1]].to_s")
        assert space.str_w(w_res) == "[[1]]"

        w_res = space.execute("return [[1], [2], [3]].to_s")
        assert space.str_w(w_res) == "[[1], [2], [3]]"

    def test_subscript(self, space):
        w_res = space.execute("return [1][0]")
        assert space.int_w(w_res) == 1

    def test_length(self, space):
        w_res = space.execute("return [1, 2, 3].length")
        assert space.int_w(w_res) == 3

    def test_plus(self, space):
        w_res = space.execute("return [1, 2] + [3]")
        assert self.unwrap(space, w_res) == [1, 2, 3]

    def test_minus(self, space):
        w_res = space.execute("return [1, 1, 2, '3'] - [1, '3']")
        assert self.unwrap(space, w_res) == [2]

    def test_lshift(self, space):
        w_res = space.execute("return [] << 1")
        assert self.unwrap(space, w_res) == [1]

    def test_zip(self, space):
        w_res = space.execute("return [1, 2, 3].zip([3, 2, 1])")
        assert self.unwrap(space, w_res) == [[1, 3], [2, 2], [3, 1]]

    def test_product(self, space):
        w_res = space.execute("return [1, 2].product([3, 4])")
        assert self.unwrap(space, w_res) == [[1, 3], [1, 4], [2, 3], [2, 4]]

    def test_size(self, space):
        w_res = space.execute("return [1, 2].size")
        assert space.int_w(w_res) == 2

    def test_range_inclusive(self, space):
        w_res = space.execute("return [1, 2, 3, 4, 5][1..2]")
        assert self.unwrap(space, w_res) == [2, 3]
        w_res = space.execute("return [1, 2, 3, 4, 5][1..-1]")
        assert self.unwrap(space, w_res) == [2, 3, 4, 5]
        w_res = space.execute("return [1, 2, 3, 4, 5][-2..-1]")
        assert self.unwrap(space, w_res) == [4, 5]

    def test_range_exclusive(self, space):
        w_res = space.execute("return [1, 2, 3, 4, 5][1...3]")
        assert self.unwrap(space, w_res) == [2, 3]
        w_res = space.execute("return [1, 2, 3, 4, 5][1...-1]")
        assert self.unwrap(space, w_res) == [2, 3, 4]
        w_res = space.execute("return [1, 2, 3, 4, 5][-2...-1]")
        assert self.unwrap(space, w_res) == [4]

    def test_range_assignment(self, space):
        w_res = space.execute("x = [1, 2, 3]; x[1..2] = 4; return x")
        assert self.unwrap(space, w_res) == [1, 4]

    def test_at(self, space):
        w_res = space.execute("return [1, 2, 3, 4, 5].at(2)")
        assert space.int_w(w_res) == 3

    def test_unshift(self, space):
        w_res = space.execute("return [1, 2].unshift(3, 4)")
        assert self.unwrap(space, w_res) == [3, 4, 1, 2]

    def test_join(self, space):
        w_res = space.execute("return [1, 'a', :b].join")
        assert space.str_w(w_res) == "1ab"
        w_res = space.execute("return [1, 'a', :b].join('--')")
        assert space.str_w(w_res) == "1--a--b"
        w_res = space.execute("return [1, 'a', :b].join(?-)")
        assert space.str_w(w_res) == "1-a-b"
        with self.raises(space, "TypeError", "can't convert Symbol into String"):
            space.execute("return [1].join(:foo)")
        w_res = space.execute("return [].join(:foo)")
        assert space.str_w(w_res) == ""
        w_res = space.execute("""
        class A; def to_str; 'A'; end; end
        return [1, 2].join(A.new)
        """)
        assert space.str_w(w_res) == "1A2"
