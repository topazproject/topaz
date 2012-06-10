from ..base import BaseRuPyPyTest

class TestNilObject(BaseRuPyPyTest):
    def test_inspect(self, ec):
        w_res = ec.space.execute(ec, "return nil.inspect")
        assert ec.space.str_w(w_res) == "nil"

    def test_nil(self, ec):
        w_res = ec.space.execute(ec, "return nil.nil?")
        assert ec.space.bool_w(w_res) == True

    def test_to_s(self, ec):
        w_res = ec.space.execute(ec, "return nil.to_s")
        assert ec.space.str_w(w_res) == ""

    def test_to_a(self, ec):
        w_res = ec.space.execute(ec, "return nil.to_a")
        assert self.unwrap(ec.space, w_res) == []

    def test_to_f(self, ec):
        w_res = ec.space.execute(ec, "return nil.to_f")
        assert ec.space.float_w(w_res) == 0.0

    def test_to_i(self, ec):
        w_res = ec.space.execute(ec, "return nil.to_i")
        assert ec.space.int_w(w_res) == 0