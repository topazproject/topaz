import math

from ..base import BaseTopazTest


class TestMath(BaseTopazTest):
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
        w_res = space.execute("return [Math.log(4, 10), Math.log(28), Math.log(3, 4)]")
        assert self.unwrap(space, w_res) == [math.log(4, 10), math.log(28), math.log(3, 4)]
