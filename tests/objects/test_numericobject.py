from ..base import BaseTopazTest


class TestNumericObject(BaseTopazTest):
    def test_to_int(self, space):
        w_res = space.execute("""
        class A < Numeric
          def to_i; 1; end
        end
        return A.new.to_int
        """)
        assert space.int_w(w_res) == 1

    def test_comparator_eq(self, space):
        w_res = space.execute("""
        class A < Numeric; end
        a = A.new
        return a <=> a
        """)
        assert space.int_w(w_res) == 0

    def test_comparator_neq(self, space):
        w_res = space.execute("""
        class A < Numeric; end
        return A.new <=> A.new
        """)
        assert w_res == space.w_nil

    def test_less_equal(self, space):
        w_res = space.execute("""
        class A < Numeric; end
        return A.new <= A.new
        """)
        assert w_res == space.w_false
        w_res = space.execute("""
        class A < Numeric; end
        a = A.new
        return a <= a
        """)
        assert w_res == space.w_true

    def test_coerce(self, space):
        w_res = space.execute("return 1.coerce(1)")
        assert self.unwrap(space, w_res) == [1, 1]
        w_res = space.execute("return 1.1.coerce(1)")
        assert self.unwrap(space, w_res) == [1.0, 1.1]
        w_res = space.execute("return 1.coerce(1.1)")
        assert self.unwrap(space, w_res) == [1.1, 1.0]
        w_res = space.execute("return 1.coerce('2')")
        assert self.unwrap(space, w_res) == [2.0, 1.0]

    def test_abs(self, space):
        w_res = space.execute("return 1.abs, -1.abs")
        assert self.unwrap(space, w_res) == [1, 1]
        w_res = space.execute("return 1.1.abs, -1.1.abs")
        assert self.unwrap(space, w_res) == [1.1, 1.1]
