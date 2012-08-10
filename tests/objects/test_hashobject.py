from ..base import BaseRuPyPyTest


class TestHashObject(BaseRuPyPyTest):
    def test_create(self, space):
        space.execute("{2 => 3, 4 => 5}")

    def test_lookup(self, space):
        w_res = space.execute("""
        x = {2 => 3}
        return x[2]
        """)
        assert self.unwrap(space, w_res) == 3

    def test_lookup_non_existing(self, space):
        w_res = space.execute("""
        x = {}
        return x[2]
        """)
        assert w_res is space.w_nil

    def test_keys(self, space):
        w_res = space.execute("""
        x = {2 => 3, "four" => 5, 1 => 3, '1' => 'a'}
        return x.keys
        """)
        assert self.unwrap(space, w_res) == [2, "four", 1, "1"]
