import math

from ..base import BaseRuPyPyTest


class TestMath(BaseRuPyPyTest):
    def test_pi(self, space):
        w_res = space.execute("return Math::PI")
        assert space.float_w(w_res) == math.pi

    def test_exp(self, space):
        w_res = space.execute("return [Math.exp(0.0), Math.exp(1)]")
        assert self.unwrap(space, w_res) == [1, math.exp(1)]
