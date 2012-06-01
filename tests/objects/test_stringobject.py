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
