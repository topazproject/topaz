class TestArrayObject(object):
    def test_to_s(self, ec):
        w_res = ec.space.execute(ec, "return [].to_s")
        assert ec.space.str_w(w_res) == "[]"

        w_res = ec.space.execute(ec, "return [[1]].to_s")
        assert ec.space.str_w(w_res) == "[[1]]"

        w_res = ec.space.execute(ec, "return [[1], [2], [3]].to_s")
        assert ec.space.str_w(w_res) == "[[1], [2], [3]]"

    def test_subscript(self, ec):
        w_res = ec.space.execute(ec, "return [1][0]")
        assert ec.space.int_w(w_res) == 1

    def test_length(self, ec):
        w_res = ec.space.execute(ec, "return [1, 2, 3].length")
        assert ec.space.int_w(w_res) == 3

    def test_plus(self, ec):
        w_res = ec.space.execute(ec, "return [1, 2] + [3]")
        assert [ec.space.int_w(w_x) for w_x in ec.space.listview(w_res)] == [1, 2, 3]

    def test_lshift(self, ec):
        w_res = ec.space.execute(ec, "return [] << 1")
        assert [ec.space.int_w(w_x) for w_x in ec.space.listview(w_res)] == [1]

    def test_zip(self, ec):
        w_res = ec.space.execute(ec, "return [1, 2, 3].zip([3, 2, 1])")
        assert [[ec.space.int_w(w_x) for w_x in ec.space.listview(w_sub)] for w_sub in ec.space.listview(w_res)] == [[1, 3], [2, 2], [3, 1]]

    def test_product(self, ec):
        w_res = ec.space.execute(ec, "return [1, 2].product([3, 4])")
        assert [[ec.space.int_w(w_x) for w_x in ec.space.listview(w_sub)] for w_sub in ec.space.listview(w_res)] == [[1, 3], [1, 4], [2, 3], [2, 4]]

    def no_test_size(self, ec):
        w_res = ec.space.execute(ec, "return [1, 2].size")
        assert ec.space.int_w(w_res) == 2

    def test_range_inclusive(self, ec):
        w_res = ec.space.execute(ec, "return [1, 2, 3, 4, 5][1..2]")
        assert [ec.space.int_w(w_x) for w_x in ec.space.listview(w_res)] == [2, 3]

    def test_range_exclusive(self, ec):
        w_res = ec.space.execute(ec, "return [1, 2, 3, 4, 5][1...3]")
        assert [ec.space.int_w(w_x) for w_x in ec.space.listview(w_res)] == [2, 3]
    