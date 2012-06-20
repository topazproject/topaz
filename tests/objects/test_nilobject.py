from ..base import BaseRuPyPyTest


class TestNilObject(BaseRuPyPyTest):
    def test_asdasd(self, space):
        w_res = space.execute("return nil")
        assert self.unwrap(space, w_res) == None
    
    def test_inspect(self, space):
        w_res = space.execute("return nil.inspect")
        assert self.unwrap(space, w_res) == "nil"

    def test_nil(self, space):
        w_res = space.execute("return nil.nil?")
        assert self.unwrap(space, w_res) == True

    def test_to_s(self, space):
        w_res = space.execute("return nil.to_s")
        assert self.unwrap(space, w_res) == ""

    def test_to_a(self, space):
        w_res = space.execute("return nil.to_a")
        assert self.unwrap(space, w_res) == []

    def test_to_f(self, space):
        w_res = space.execute("return nil.to_f")
        assert self.unwrap(space, w_res) == 0.0

    def test_to_i(self, space):
        w_res = space.execute("return nil.to_i")
        assert self.unwrap(space, w_res) == 0