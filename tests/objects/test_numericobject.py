from ..base import BaseRuPyPyTest


class TestNumericObject(BaseRuPyPyTest):
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
