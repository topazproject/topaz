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

    def test_xor(self, space):
        assert space.execute("return true ^ nil") is space.w_true
        assert space.execute("return true ^ false") is space.w_true
        assert space.execute("return true ^ true") is space.w_false
        assert space.execute("return true ^ 1") is space.w_false

class TestFalseObject(BaseRuPyPyTest):
    def test_to_s(self, space):
        w_res = space.execute("return false.to_s")
        assert space.str_w(w_res) == "false"

    def test_eql(self, space):
        w_res = space.execute("return false == false")
        assert self.unwrap(space, w_res) is True

        w_res = space.execute("return false == true")
        assert self.unwrap(space, w_res) is False

    def test_xor(self, space):
        assert space.execute("return false ^ nil") is space.w_false
        assert space.execute("return false ^ false") is space.w_false
        assert space.execute("return false ^ true") is space.w_true
        assert space.execute("return false ^ 1") is space.w_true
