from ..base import BaseRuPyPyTest


class TestTrueObject(BaseRuPyPyTest):
    def test_to_s(self, space):
        w_res = space.execute("return true.to_s")
        assert space.str_w(w_res) == "true"

    def test_eql(self, space):
        w_res = space.execute("return true == false")
        assert self.unwrap(space, w_res) is False

        w_res = space.execute("return true == true")
        assert self.unwrap(space, w_res) is True

class TestFalseObject(BaseRuPyPyTest):
    def test_to_s(self, space):
        w_res = space.execute("return false.to_s")
        assert space.str_w(w_res) == "false"

    def test_eql(self, space):
        w_res = space.execute("return false == false")
        assert self.unwrap(space, w_res) is True

        w_res = space.execute("return false == true")
        assert self.unwrap(space, w_res) is False
