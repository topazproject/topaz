from ..base import BaseRuPyPyTest


class TestNilObject(BaseRuPyPyTest):
    def test_inspect(self, space):
        w_res = space.execute("return nil.inspect")
        assert space.str_w(w_res) == "nil"

    def test_nil(self, space):
        w_res = space.execute("return nil.nil?")
        print "w_res", w_res
        assert space.bool_w(w_res) == True

    def test_to_s(self, space):
        w_res = space.execute("return nil.to_s")
        assert space.str_w(w_res) == ""

    def test_to_a(self, space):
        w_res = space.execute("return nil.to_a")
        assert self.unwrap(space, w_res) == []

    def test_to_f(self, space):
        w_res = space.execute("return nil.to_f")
        assert space.float_w(w_res) == 0.0

    def test_to_i(self, space):
        w_res = space.execute("return nil.to_i")
        assert space.int_w(w_res) == 0