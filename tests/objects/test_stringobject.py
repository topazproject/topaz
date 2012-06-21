from ..base import BaseRuPyPyTest


class TestStringObject(BaseRuPyPyTest):
    def test_lshift(self, space):
        w_res = space.execute('return "abc" << "def" << "ghi"')
        assert space.str_w(w_res) == "abcdefghi"

    def test_plus(self, space):
        w_res = space.execute('return "abc" + "def" + "ghi"')
        assert space.str_w(w_res) == "abcdefghi"

    def test_to_s(self, space):
        w_res = space.execute('return "ABC".to_s')
        assert space.str_w(w_res) == "ABC"

    def test_length(self, space):
        w_res = space.execute("return 'ABC'.length")
        assert space.int_w(w_res) == 3

    def test_comparator_lt(self, space):
        w_res = space.execute("return 'a' <=> 'b'")
        assert space.int_w(w_res) == -1

    def test_comparator_eq(self, space):
        w_res = space.execute("return 'a' <=> 'a'")
        assert space.int_w(w_res) == 0

    def test_comparator_gt(self, space):
        w_res = space.execute("return 'b' <=> 'a'")
        assert space.int_w(w_res) == 1

    def test_subscript(self, space):
        w_res = space.execute("return 'abcdefg'[1]")
        assert space.str_w(w_res) == "b"

    def test_range_inclusive(self, space):
        w_res = space.execute("return 'abcdefg'[1..2]")
        assert space.str_w(w_res) == "bc"

    def test_range_exclusive(self, space):
        w_res = space.execute("return 'abcdefg'[1...3]")
        assert space.str_w(w_res) == "bc"

    def test_hash(self, space):
        w_res = space.execute("""
        return ['abc'.hash, ('a' << 'b' << 'c').hash]
        """)
        h1, h2 = self.unwrap(space, w_res)
        assert h1 == h2

    def test_edge_indices(self, space):
        w_res = space.execute("return 'hello'[5]")
        assert self.unwrap(space, w_res) == None

    def test_1(self, space):
        w_res = space.execute("return 'hello'[-2]")
        assert self.unwrap(space, w_res) == "l"

    def test_2(self, space):
        w_res = space.execute("return 'hello'[-6]")
        assert self.unwrap(space, w_res) == None

    def test_3(self, space):
        w_res = space.execute("return 'hello'[-2..0]")
        assert self.unwrap(space, w_res) == ""

    def test_4(self, space):
        w_res = space.execute("return 'hello'[5..5]")
        assert self.unwrap(space, w_res) == ""

    def test_5(self, space):
        w_res = space.execute("return 'hello'[5..8]")
        assert self.unwrap(space, w_res) == ""

    def test_6(self, space):
        w_res = space.execute("return 'hello'[-3..-2]")
        assert self.unwrap(space, w_res) == "ll"

    def test_7(self, space):
        w_res = space.execute("return 'hello'[-2..-1]")
        assert self.unwrap(space, w_res) == "lo"

    def test_8(self, space):
        w_res = space.execute("return 'hello'[4..2]")
        assert space.str_w(w_res) == ""

    def test_9(self, space):
        w_res = space.execute("return 'hello'[8..10]")
        assert self.unwrap(space, w_res) == None
        
        #w_res = space.execute("return 'hello'[3..-2]")
        #assert self.unwrap(space, w_res) == "l"
