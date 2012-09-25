from ..base import BaseRuPyPyTest


class TestFixnumObject(BaseRuPyPyTest):
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

    def test_division(self, space):
        w_res = space.execute("return 3 / 5")
        assert space.int_w(w_res) == 0

    def test_equal(self, space):
        w_res = space.execute("return 1 == 1")
        assert w_res is space.w_true
        w_res = space.execute("""
        class A
          def ==(o); 'hi'; end
        end
        return 1 == A.new
        """)
        assert space.str_w(w_res) == 'hi'
        w_res = space.execute("return 1 == '1'")
        assert w_res is space.w_false

    def test_not_equal(self, space):
        w_res = space.execute("return 1 != 1")
        assert w_res is space.w_false
        w_res = space.execute("return 1 != '1'")
        assert w_res is space.w_true
        w_res = space.execute("""
        class A
          def ==(o); 'hi'; end
        end
        return 1 != A.new
        """)
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

    def test_comparator_float(self, space):
        w_res = space.execute("return 1 <=> 1.1")
        assert space.int_w(w_res) == -1

    def test_comparator_other_type(self, space):
        w_res = space.execute("return 1 <=> '1'")
        assert w_res is space.w_nil

    def test_to_i(self, space):
        w_res = space.execute("return [1.to_i, 1.to_int]")
        assert self.unwrap(space, w_res) == [1, 1]

    def test_nonzero(self, space):
        w_res = space.execute("return [2.nonzero?, 0.nonzero?]")
        assert self.unwrap(space, w_res) == [True, False]

    def test_object_id(self, space):
        w_res = space.execute("return 2.object_id, 2.object_id")
        id_1, id_2 = self.unwrap(space, w_res)
        assert id_1 == id_2

    def test___id__(self, space):
        w_res = space.execute("return 2.__id__, 2.__id__")
        id_1, id_2 = self.unwrap(space, w_res)
        assert id_1 == id_2

    def test_ivar(self, space):
        w_res = space.execute("""
        class Fixnum
          def set; @foo = -1; end
          def get; @foo; end
        end
        2.set
        return 2.get, 2.get, 3.get
        """)
        [x, y, z] = self.unwrap(space, w_res)
        assert x == y == -1
        assert z is None

    def test_succ(self, space):
        w_res = space.execute("return -1.succ")
        assert self.unwrap(space, w_res) == 0
        
        w_res = space.execute("return 7.succ")
        assert self.unwrap(space, w_res) == 8
