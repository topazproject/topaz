class TestArrayObject(object):
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
        assert [space.int_w(w_x) for w_x in space.listview(w_res)] == [1, 2, 3]

    def test_lshift(self, space):
        w_res = space.execute("return [] << 1")
        assert [space.int_w(w_x) for w_x in space.listview(w_res)] == [1]

    def test_zip(self, space):
        w_res = space.execute("return [1, 2, 3].zip([3, 2, 1])")
        assert [[space.int_w(w_x) for w_x in space.listview(w_sub)] for w_sub in space.listview(w_res)] == [[1, 3], [2, 2], [3, 1]]

    def test_product(self, space):
        w_res = space.execute("return [1, 2].product([3, 4])")
        assert [[space.int_w(w_x) for w_x in space.listview(w_sub)] for w_sub in space.listview(w_res)] == [[1, 3], [1, 4], [2, 3], [2, 4]]
