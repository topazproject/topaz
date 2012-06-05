from ..base import BaseRuPyPyTest


class TestHashObject(BaseRuPyPyTest):
    def test_to_s(self, ec):
        w_res = ec.space.execute(ec, "return {}.to_s")
        assert ec.space.str_w(w_res) == "{}"

        w_res = ec.space.execute(ec, "return {1 => 2}.to_s")
        assert ec.space.str_w(w_res) == "{1 => 2}"

        w_res = ec.space.execute(ec, "return {1 => 2, 3 => 4}.to_s")
        assert ec.space.str_w(w_res) == "{1 => 2, 3 => 4}"

    def test_at(self, ec):
        w_res = ec.space.execute(ec, "return {1 => 2}[1]")
        assert ec.space.int_w(w_res) == 2

        w_res = ec.space.execute(ec, "return {'a' => 2}['a']")
        assert ec.space.int_w(w_res) == 2

        w_res = ec.space.execute(ec, "return {:a => 2}[:a]")
        assert ec.space.int_w(w_res) == 2

        w_res = ec.space.execute(ec, "return {1.1 => 2}[1.1]")
        assert ec.space.int_w(w_res) == 2

    def test_at_put(self, ec):
        w_res = ec.space.execute(ec, "return [1, 2, 3, 4, 5].at(2)")
        assert ec.space.int_w(w_res) == 3

    def test_length(self, ec):
        w_res = ec.space.execute(ec, "return {1 => 2, 3 => 4}.length")
        assert ec.space.int_w(w_res) == 2

    def test_size(self, ec):
        w_res = ec.space.execute(ec, "return {1 => 2, 3 => 4}.size")
        assert ec.space.int_w(w_res) == 2

    def test_keys(self, ec):
        w_res = ec.space.execute(ec, "return {1 => 2, 3 => 4}.keys")
        assert [ec.space.int_w(i) for i in ec.space.listview(w_res)] == [1, 3]

    def test_values(self, ec):
        w_res = ec.space.execute(ec, "return {1 => 2, 3 => 4}.values")
        assert [ec.space.int_w(i) for i in ec.space.listview(w_res)] == [2, 4]
