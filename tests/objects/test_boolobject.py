from ..base import BaseTopazTest


class TestTrueObject(BaseTopazTest):
    def test_name(self, space):
        space.execute("TrueClass")

    def test_to_s(self, space):
        w_res = space.execute("return true.to_s")
        assert space.str_w(w_res) == "true"

    def test_inspect(self, space):
        w_res = space.execute("return true.inspect")
        assert space.str_w(w_res) == "true"

    def test_eql(self, space):
        w_res = space.execute("return true == false")
        assert self.unwrap(space, w_res) is False

        w_res = space.execute("return true == true")
        assert self.unwrap(space, w_res) is True

    def test_and(self, space):
        w_res = space.execute("return true & 3")
        assert self.unwrap(space, w_res) is True
        w_res = space.execute("return true & false")
        assert self.unwrap(space, w_res) is False

    def test_or(self, space):
        w_res = space.execute("return true | 3")
        assert w_res is space.w_true
        w_res = space.execute("return true | nil")
        assert w_res is space.w_true

    def test_xor(self, space):
        w_res = space.execute("return true ^ nil")
        assert self.unwrap(space, w_res) is True
        w_res = space.execute("return true ^ false")
        assert self.unwrap(space, w_res) is True
        w_res = space.execute("return true ^ true")
        assert self.unwrap(space, w_res) is False
        w_res = space.execute("return true ^ 1")
        assert self.unwrap(space, w_res) is False

    def test_singleton_class(self, space):
        w_res = space.execute("return true.singleton_class == TrueClass")
        assert self.unwrap(space, w_res)


class TestFalseObject(BaseTopazTest):
    def test_name(self, space):
        space.execute("FalseClass")

    def test_to_s(self, space):
        w_res = space.execute("return false.to_s")
        assert space.str_w(w_res) == "false"

    def test_inspect(self, space):
        w_res = space.execute("return false.inspect")
        assert space.str_w(w_res) == "false"

    def test_eql(self, space):
        w_res = space.execute("return false == false")
        assert self.unwrap(space, w_res) is True

        w_res = space.execute("return false == true")
        assert self.unwrap(space, w_res) is False

    def test_and(self, space):
        w_res = space.execute("return false & 3")
        assert self.unwrap(space, w_res) is False
        w_res = space.execute("return false & false")
        assert self.unwrap(space, w_res) is False

    def test_or(self, space):
        w_res = space.execute("return false | 3")
        assert self.unwrap(space, w_res) is True
        w_res = space.execute("return false | nil")
        assert self.unwrap(space, w_res) is False

    def test_xor(self, space):
        w_res = space.execute("return false ^ nil")
        assert self.unwrap(space, w_res) is False
        w_res = space.execute("return false ^ false")
        assert self.unwrap(space, w_res) is False
        w_res = space.execute("return false ^ true")
        assert self.unwrap(space, w_res) is True
        w_res = space.execute("return false ^ 1")
        assert self.unwrap(space, w_res) is True

    def test_singleton_class(self, space):
        w_res = space.execute("return false.singleton_class == FalseClass")
        assert self.unwrap(space, w_res) is True
