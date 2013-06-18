from topaz.objects.randomobject import W_RandomObject

from ..base import BaseTopazTest


class TestRandomObject(BaseTopazTest):
    def test_new(self, space):
        w_res = space.execute("return Random.new")
        assert isinstance(w_res, W_RandomObject)

    def test_rand(self, space):
        w_res = space.execute("return Random.new.rand")
        assert 0 < space.float_w(w_res) < 1

    def test_subclass(self, space):
        w_res = space.execute("""
        class SubRandom < Random
          def better_rand
            # http://xkcd.com/221/
            4
          end
        end
        c = SubRandom.new
        return [c.rand, c.better_rand]
        """)
        rand, better_rand = self.unwrap(space, w_res)
        assert 0 < rand < 1
        assert better_rand == 4
