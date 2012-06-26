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

    def test_exceptions(self, space):
        w_res = space.execute("return TypeError.exception('msg')")
        assert isinstance(w_res, W_TypeError)
        w_res = space.execute("""
        e1 = TypeError.new('msg')
        e2 = e1.exception
        e3 = e1.exception('new msg')
        return [e1, e2, e3]
        """)
        res = space.listview(w_res)
        assert res[0] is res[1]
        assert res[0] is not res[2]
