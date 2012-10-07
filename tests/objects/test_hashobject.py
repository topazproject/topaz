from ..base import BaseRuPyPyTest


class TestHashObject(BaseRuPyPyTest):
    def test_name(self, space):
        space.execute("Hash")

    def test_create(self, space):
        space.execute("{2 => 3, 4 => 5}")

    def test_new(self, space):
        w_res = space.execute("return Hash.new.keys")
        assert self.unwrap(space, w_res) == []

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

    def test_each(self, space):
        w_res = space.execute("""
        x = {2 => 3, "four" => 5, 3 => 2}
        result = []
        x.each do |k, v|
            result << [k, v]
        end
        return result
        """)
        assert self.unwrap(space, w_res) == [[2, 3], ["four", 5], [3, 2]]
        w_res = space.execute("""
        result = []
        {2 => 3}.each_pair do |k, v|
            result << [k, v]
        end
        return result
        """)
        assert self.unwrap(space, w_res) == [[2, 3]]
