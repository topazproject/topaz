from rupypy.objects.exceptionobject import W_TypeError

from ..base import BaseRuPyPyTest


class TestExceptionObject(BaseRuPyPyTest):
    def test_new(self, space):
        w_res = space.execute("return TypeError.new")
        assert isinstance(w_res, W_TypeError)
        w_res = space.execute("return TypeError.new('msg')")
        assert isinstance(w_res, W_TypeError)

    def test_to_s(self, space):
        w_res = space.execute("return TypeError.new('msg').to_s")
        assert space.str_w(w_res) == "msg"
