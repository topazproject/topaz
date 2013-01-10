from ..base import BaseTopazTest


class TestNilObject(BaseTopazTest):
    def test_name(self, space):
        space.execute("NilClass")

    def test_to_s(self, space):
        w_res = space.execute("return nil.to_s")
        assert space.str_w(w_res) == ""

    def test_inspect(self, space):
        w_res = space.execute("return nil.inspect")
        assert space.str_w(w_res) == "nil"

    def test_nilp(self, space):
        w_res = space.execute("return nil.nil?")
        assert w_res == space.w_true
        w_res = space.execute("return 1.nil?")
        assert w_res == space.w_false

    def test_to_i(self, space):
        w_res = space.execute("return nil.to_i")
        assert space.int_w(w_res) == 0

    def test_to_f(self, space):
        w_res = space.execute("return nil.to_f")
        assert space.float_w(w_res) == 0.0

    def test_to_a(self, space):
        w_res = space.execute("return nil.to_a")
        assert self.unwrap(space, w_res) == []

    def test_and(self, space):
        w_res = space.execute("return nil & true")
        assert w_res is space.w_false

    def test_or(self, space):
        w_res = space.execute("return nil | 4")
        assert w_res is space.w_true
        w_res = space.execute("return nil | false")
        assert w_res is space.w_false

    def test_xor(self, space):
        w_res = space.execute("return nil ^ 4")
        assert w_res is space.w_true
        w_res = space.execute("return nil ^ false")
        assert w_res is space.w_false

    def test_singleton_class(self, space):
        w_res = space.execute("return nil.singleton_class == NilClass")
        assert w_res is space.w_true
