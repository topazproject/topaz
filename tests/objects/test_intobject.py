class TestIntObject(object):
    def test_multiplication(self, ec):
        w_res = ec.space.execute(ec, "return 2 * 3")
        assert ec.space.int_w(w_res) == 6

    def test_subtraction(self, ec):
        w_res = ec.space.execute(ec, "return 2 - 3")
        assert ec.space.int_w(w_res) == -1

        w_res = ec.space.execute(ec, "return 2 - 3.5")
        assert ec.space.float_w(w_res) == -1.5

    def test_equal(self, ec):
        w_res = ec.space.execute(ec, "return 1 == 1")
        assert w_res is ec.space.w_true

    def test_not_equal(self, ec):
        w_res = ec.space.execute(ec, "return 1 != 1")
        assert w_res is ec.space.w_false

    def test_less(self, ec):
        w_res = ec.space.execute(ec, "return 1 < 2")
        assert w_res is ec.space.w_true

    def test_greater(self, ec):
        w_res = ec.space.execute(ec, "return 1 > 2")
        assert w_res is ec.space.w_false

    def test_times(self, ec):
        w_res = ec.space.execute(ec, """
        res = []
        3.times do |x|
            res << x
        end
        return res
        """)
        assert [ec.space.int_w(w_x) for w_x in ec.space.listview(w_res)] == [0, 1, 2]
