class TestIntObject(object):
    def test_multiplication(self, space):
        w_res = space.execute("return 2 * 3")
        assert space.int_w(w_res) == 6

    def test_subtraction(self, space):
        w_res = space.execute("return 2 - 3")
        assert space.int_w(w_res) == -1

    def test_equal(self, space):
        w_res = space.execute("return 1 == 1")
        assert w_res is space.w_true

    def test_not_equal(self, space):
        w_res = space.execute("return 1 != 1")
        assert w_res is space.w_false

    def test_less(self, space):
        w_res = space.execute("return 1 < 2")
        assert w_res is space.w_true

    def test_greater(self, space):
        w_res = space.execute("return 1 > 2")
        assert w_res is space.w_false
