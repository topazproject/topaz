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

    def test_object_id(self, space):
        w_res = space.listview(space.execute("return 2.object_id, 2.object_id"))
        assert w_res[0].intvalue == w_res[1].intvalue

    def test___id__(self, space):
        res = space.listview(space.execute("return 2.__id__, 2.__id__"))
        assert res[0].intvalue == res[1].intvalue

    def test_ivar(self, space):
        res = space.listview(space.execute("""
        class Fixnum
          def set; @foo = -1; end
          def get; @foo; end
        end
        2.set
        return 2.get, 2.get, 3.get
        """))
        assert res[0].intvalue == res[1].intvalue == -1
        assert res[2] == space.w_nil
