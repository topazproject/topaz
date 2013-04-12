from ..base import BaseTopazTest


class TestHashObject(BaseTopazTest):
    def test_name(self, space):
        space.execute("Hash")

    def test_create(self, space):
        space.execute("{2 => 3, 4 => 5}")

    def test_subscript_create(self, space):
        w_res = space.execute("return Hash[].length")
        assert space.int_w(w_res) == 0

    def test_subscript_create_hash(self, space):
        w_res = space.execute("return Hash[{2 => 3}][2]")
        assert space.int_w(w_res) == 3

    def test_default_value(self, space):
        w_res = space.execute("""
        x = Hash.new 5
        return x[2]
        """)
        assert space.int_w(w_res) == 5
        w_res = space.execute("""
        x = Hash.new 5
        x[2] = 12
        return x[2]
        """)
        assert space.int_w(w_res) == 12
        w_res = space.execute("return Hash.new(2).default")
        assert space.int_w(w_res) == 2

        w_res = space.execute("""
        class Foo < Hash
          def default key
            key * 2
          end
        end

        return Foo.new[6]
        """)
        assert space.int_w(w_res) == 12

    def test_default_proc(self, space):
        w_res = space.execute("""
        x = Hash.new { |h, k| h[k + 2] = k }
        return [x[2], x[4]]
        """)
        assert self.unwrap(space, w_res) == [2, 2]

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

    def test_clear(self, space):
        w_res = space.execute("""
        x = {2 => 3}
        x.clear
        return x.keys
        """)
        assert self.unwrap(space, w_res) == []

    def test_lookup_eql(self, space):
        w_res = space.execute("return {1 => 2}[1.0]")
        assert w_res is space.w_nil

    def test_fetch_existing(self, space):
        w_res = space.execute("return {'a' => 1}.fetch('a')")
        assert self.unwrap(space, w_res) == 1

    def test_fetch_non_existing_with_value(self, space):
        w_res = space.execute("return {}.fetch('a', 1)")
        assert self.unwrap(space, w_res) == 1

    def test_fetch_non_existing_with_block(self, space):
        w_res = space.execute("return {}.fetch('a') { 1 }")
        assert self.unwrap(space, w_res) == 1

    def test_fetch_non_existing_with_no_value_and_no_block(self, space):
        with self.raises(space, "KeyError"):
            space.execute("return {}.fetch('a')")

    def test_fetch_no_args(self, space):
        with self.raises(space, "ArgumentError"):
            space.execute("{}.fetch()")

    def test_delete(self, space):
        w_res = space.execute("""
        x = {2 => 3, 4 => 5}
        return [x.delete(2), x.keys, x.delete(123)]
        """)
        assert self.unwrap(space, w_res) == [3, [4], None]

    def test_delete_with_block(self, space):
        w_res = space.execute("return {}.delete(3) { |a| a }")
        assert space.int_w(w_res) == 3

    def test_replace(self, space):
        w_res = space.execute("return {}.replace({'a' => 1}).keys")
        assert self.unwrap(space, w_res) == ['a']

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

    def test_each_key(self, space):
        w_res = space.execute("""
        x = {2 => 3, "four" => 5, 3 => 2}
        result = []
        x.each_key do |k|
          result << k
        end
        return result
        """)
        assert self.unwrap(space, w_res) == [2, "four", 3]

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

    def test_size(self, space):
        w_res = space.execute("return {}.size")
        assert space.int_w(w_res) == 0
        w_res = space.execute("return {:a => 2}.size")
        assert space.int_w(w_res) == 1

    def test_emptyp(self, space):
        w_res = space.execute("return {}.empty?")
        assert w_res is space.w_true
        w_res = space.execute("return {1 => 2}.empty?")
        assert w_res is space.w_false

    def test_equal(self, space):
        w_res = space.execute("return {} == nil")
        assert w_res is space.w_false
        w_res = space.execute("return {1 => 2, 2 => 3} == {2 => 3, 1 => 2}")
        assert w_res is space.w_true
        w_res = space.execute("return {} == {}")
        assert w_res is space.w_true
        w_res = space.execute("return {} == {1 => 2}")
        assert w_res is space.w_false
        w_res = space.execute("""
        h = {}
        return h == h
        """)
        assert w_res is space.w_true

    def test_shift(self, space):
        w_res = space.execute("return {}.shift")
        assert w_res is space.w_nil
        w_res = space.execute("return {3 => 4}.shift")
        assert self.unwrap(space, w_res) == [3, 4]

    def test_dup(self, space):
        w_res = space.execute("return {2 => 4}.dup.length")
        assert space.int_w(w_res) == 1
