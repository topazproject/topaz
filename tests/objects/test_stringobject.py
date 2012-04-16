class TestStringObject(object):
    def test_lshift(self, space):
        w_res = space.execute('return "abc" << "def" << "ghi"')
        assert space.str_w(w_res) == "abcdefghi"

    def test_plus(self, space):
        w_res = space.execute('return "abc" + "def" + "ghi"')
        assert space.str_w(w_res) == "abcdefghi"