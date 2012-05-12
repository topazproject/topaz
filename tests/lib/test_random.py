from rupypy.lib.random import W_Random


class TestRandom(object):
    def test_new(self, ec):
        w_res = ec.space.execute(ec, "return Random.new")
        assert isinstance(w_res, W_Random)

    def test_rand(self, ec):
        w_res = ec.space.execute(ec, "return Random.new.rand")
        assert 0 < ec.space.float_w(w_res) < 1
