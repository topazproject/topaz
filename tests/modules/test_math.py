import math


class TestMath(object):
    def test_expr(self, ec):
        w_res = ec.space.execute(ec, "return [Math.exp(0.0), Math.exp(1)]")
        assert [ec.space.float_w(w_x) for w_x in ec.space.listview(w_res)] == [1, math.e]
