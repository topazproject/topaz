from rupypy.lib.random import W_Random


class TestRandom(object):
    def test_new(self, space):
        w_res = space.execute("return Random.new")
        assert isinstance(w_res, W_Random)

    def test_rand(self, space):
        w_res = space.execute("return Random.new.rand")
        assert 0 < space.float_w(w_res) < 1
