from rupypy.lib.random import W_Random

from ..base import BaseRuPyPyTest


class TestRandom(BaseRuPyPyTest):
    def test_new(self, space):
        w_res = space.execute("return Random.new")
        assert isinstance(w_res, W_Random)

    def test_rand(self, space):
        w_res = space.execute("return Random.new.rand")
        assert 0 < space.float_w(w_res) < 1

    def test_subclass(self, space):
        w_res = space.execute("""
        class SubRandom < Random
            def better_rand
                4 # http://xkcd.com/221/
            end
        end
        c = SubRandom.new
        return [c.rand, c.better_rand]
        """)
        res = self.unwrap(space, w_res)
        assert 0 < res[0] < 1
        assert res[1] == 4
