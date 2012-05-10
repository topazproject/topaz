import math


class TestMath(object):
    def test_expr(self, space):
        w_res = space.execute("return [Math.exp(0.0), Math.exp(1)]")
        assert [space.float_w(w_x) for w_x in space.listview(w_res)] == [1, math.e]
