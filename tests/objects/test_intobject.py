class TestFixnumObject(object):
    def test_addition(self, space):
        w_res = space.execute("return 1 + 2")
        assert space.int_w(w_res) == 3

        w_res = space.execute("return 1 + 2.5")
        assert space.float_w(w_res) == 3.5

    def test_multiplication(self, space):
        w_res = space.execute("return 2 * 3")
        assert space.int_w(w_res) == 6

    def test_subtraction(self, space):
        w_res = space.execute("return 2 - 3")
        assert space.int_w(w_res) == -1

        w_res = space.execute("return 2 - 3.5")
        assert space.float_w(w_res) == -1.5

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

    def test_times(self, space):
        w_res = space.execute("""
        res = []
        3.times do |x|
            res << x
        end
        return res
        """)
        assert [space.int_w(w_x) for w_x in space.listview(w_res)] == [0, 1, 2]

    def test_comparator_lt(self, space):
        w_res = space.execute("return 1 <=> 2")
        assert space.int_w(w_res) == -1

    def test_comparator_eq(self, space):
        w_res = space.execute("return 1 <=> 1")
        assert space.int_w(w_res) == 0

    def test_comparator_gt(self, space):
        w_res = space.execute("return 2 <=> 1")
        assert space.int_w(w_res) == 1
