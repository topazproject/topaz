class TestArrayObject(object):
    def test_to_s(self, space):
        w_res = space.execute("return [[1], [2], [3]].to_s")
        assert space.str_w(w_res) == "123"

    def test_subscript(self, space):
        w_res = space.execute("return [1][0]")
        assert space.int_w(w_res) == 1