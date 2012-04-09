from rupypy.objects.boolobject import W_TrueObject


class TestInterpreter(object):
    def test_add(self, space):
        w_res = space.execute("1 + 1")
        assert isinstance(w_res, W_TrueObject)