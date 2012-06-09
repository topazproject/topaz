class TestStringObject(object):
    def test_lshift(self, ec):
        w_res = ec.space.execute(ec, 'return "abc" << "def" << "ghi"')
        assert ec.space.str_w(w_res) == "abcdefghi"

    def test_plus(self, ec):
        w_res = ec.space.execute(ec, 'return "abc" + "def" + "ghi"')
        assert ec.space.str_w(w_res) == "abcdefghi"

    def test_to_s(self, ec):
        w_res = ec.space.execute(ec, 'return "ABC".to_s')
        assert ec.space.str_w(w_res) == "ABC"

    def test_length(self, ec):
        w_res = ec.space.execute(ec, "return 'ABC'.length")
        assert ec.space.int_w(w_res) == 3

    def test_comparator_lt(self, ec):
        w_res = ec.space.execute(ec, "return 'a' <=> 'b'")
        assert ec.space.int_w(w_res) == -1

    def test_comparator_eq(self, ec):
        w_res = ec.space.execute(ec, "return 'a' <=> 'a'")
        assert ec.space.int_w(w_res) == 0

    def test_comparator_gt(self, ec):
        w_res = ec.space.execute(ec, "return 'b' <=> 'a'")
        assert ec.space.int_w(w_res) == 1

    def test_subscript(self, ec):
        w_res = ec.space.execute(ec, "return 'abcdefg'[1]")
        assert ec.space.str_w(w_res) == "b"

    def test_range_inclusive(self, ec):
        w_res = ec.space.execute(ec, "return 'abcdefg'[1..2]")
        assert ec.space.str_w(w_res) == "bc"

    def test_range_exclusive(self, ec):
        w_res = ec.space.execute(ec, "return 'abcdefg'[1...3]")
        assert ec.space.str_w(w_res) == "bc"
