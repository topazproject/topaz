from ..base import BaseRuPyPyTest


class TestTrueObject(BaseRuPyPyTest):
    def test_to_s(self, space):
        w_res = space.execute("return true.to_s")
        assert space.str_w(w_res) == "true"

    def test_true(self, space):
        w_res = space.execute("return true")
        assert self.unwrap(space, w_res) == True

class TestFalseObject(BaseRuPyPyTest):
    def test_to_s(self, space):
        w_res = space.execute("return false.to_s")
        assert space.str_w(w_res) == "false"

    def test_false(self, space):
        w_res = space.execute("return false")
        assert self.unwrap(space, w_res) == False
