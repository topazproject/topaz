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

    def test_delete(self, space):
        w_res = space.execute("""
        x = {2 => 3, 4 => 5}
        return [x.delete(2), x.keys, x.delete(123)]
        """)
        assert self.unwrap(space, w_res) == [3, [4], None]

    def test_keys(self, space):
        w_res = space.execute("""
        x = {2 => 3, "four" => 5, 1 => 3, '1' => 'a'}
        return x.keys
        """)
        assert self.unwrap(space, w_res) == [2, "four", 1, "1"]

    def test_values(self, space):
        w_res = space.execute("""
        x = {2 => 3, "four" => 5, 1 => 3, '1' => 'a'}
        return x.values
        """)
        assert self.unwrap(space, w_res) == [3, 5, 3, "a"]

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

    def test_includep(self, space):
        w_res = space.execute("""
        h = { "a" => 100, "b" => 200 }
        return h.include?("a"), h.include?("z"), h.key?("a"), h.key?("z"), h.has_key?("a"), h.has_key?("z"), h.member?("a"), h.member?("z")
        """)
        assert self.unwrap(space, w_res) == [True, False, True, False, True, False, True, False]
