from ..base import BaseTopazTest
import pytest


class TestMarshal(BaseTopazTest):
    def test_integer(self, space):
        w_res = space.execute("return Marshal.load(Marshal.dump(5))")
        assert space.int_w(w_res) == 5

    def test_string(self, space):
        w_res = space.execute("return Marshal.load(Marshal.dump('asd'))")
        assert space.str_w(w_res) == "asd"

    def test_constants(self, space):
        w_res = space.execute("return Marshal.load(Marshal.dump(true))")
        assert space.is_true(w_res)

        w_res = space.execute("return Marshal.load(Marshal.dump(false))")
        assert not space.is_true(w_res)

        w_res = space.execute("return Marshal.load(Marshal.dump(nil))")
        assert w_res == space.w_nil

    def test_array(self, space):
        w_res = space.execute("return Marshal.load(Marshal.dump([1,2,3]))")
        assert self.unwrap(space, w_res) == [1, 2, 3]

        w_res = space.execute("return Marshal.load(Marshal.dump([1,[2,3],4]))")
        assert self.unwrap(space, w_res) == [1, [2, 3], 4]

    #@pytest.mark.xfail
    def test_hash(self, space):
        w_res = space.execute("return Marshal.load(Marshal.dump({1 => 2}))")
        assert self.unwrap(space, w_res) == {1: 2}

    @pytest.mark.xfail
    def test_symbol(self, space):
        w_res = space.execute("return Marshal.load(Marshal.dump(:ab)).inspect")
        assert self.unwrap(space, w_res) == ":ab"
