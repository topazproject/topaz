import math

from ..base import BaseTopazTest


class TestMath(BaseTopazTest):
    def assert_float_equal(self, result, expected, eps=1e-15):
        assert abs(result - expected) < eps

    def test_domain_error(self, space):
        space.execute("Math::DomainError")

    def test_pi(self, space):
        w_res = space.execute("return Math::PI")
        assert space.float_w(w_res) == math.pi

    def test_exp(self, space):
        w_res = space.execute("return [Math.exp(0.0), Math.exp(1)]")
        assert self.unwrap(space, w_res) == [1, math.exp(1)]

    def test_sqrt(self, space):
        w_res = space.execute("return [Math.sqrt(4), Math.sqrt(28)]")
        assert self.unwrap(space, w_res) == [2, math.sqrt(28)]

    def test_e(self, space):
        w_res = space.execute("return Math::E")
        assert space.float_w(w_res) == math.e

    def test_log(self, space):
        w_res = space.execute("return Math.log(4, 10)")
        self.assert_float_equal(space.float_w(w_res), math.log(4, 10))

        w_res = space.execute("return Math.log(28)")
        self.assert_float_equal(space.float_w(w_res), math.log(28))

        w_res = space.execute("return Math.log(3, 4)")
        self.assert_float_equal(space.float_w(w_res), math.log(3, 4))

    def test_gamma(self, space):
        w_res = space.execute("return Math.gamma(5.0)")
        self.assert_float_equal(space.float_w(w_res), 24.0)

        w_res = space.execute("return Math.gamma(6.0)")
        self.assert_float_equal(space.float_w(w_res), 120.0)

        w_res = space.execute("return Math.gamma(0.5)")
        self.assert_float_equal(space.float_w(w_res), math.pi ** 0.5)

        w_res = space.execute("return Math.gamma(1000)")
        assert space.float_w(w_res) == float('inf')

        w_res = space.execute("return Math.gamma(0.0)")
        assert space.float_w(w_res) == float('inf')

        w_res = space.execute("return Math.gamma(-0.0)")
        assert space.float_w(w_res) == float('-inf')

        # inf
        w_res = space.execute("return Math.gamma(1e1000)")
        assert space.float_w(w_res) == float('inf')

        with self.raises(space, "DomainError", 'Numerical argument is out of domain - "gamma"'):
            space.execute("""Math.gamma(-1)""")
        with self.raises(space, "DomainError", 'Numerical argument is out of domain - "gamma"'):
            # -inf
            space.execute("""Math.gamma(-1e1000)""")

        # nan
        w_res = space.execute("return Math.gamma(1e1000 - 1e1000)")
        assert math.isnan(space.float_w(w_res))
