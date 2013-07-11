import math
import sys

from ..base import BaseTopazTest


class TestFloatObject(BaseTopazTest):
    def test_max(self, space):
        assert space.float_w(space.execute("return Float::MAX")) == sys.float_info.max

    def test_min(self, space):
        assert space.float_w(space.execute("return Float::MIN")) == sys.float_info.min

    def test_infinity(self, space):
        assert space.float_w(space.execute("return Float::INFINITY")) == float("infinity")

    def test_nan_constant(self, space):
        assert math.isnan(space.float_w(space.execute("return Float::NAN")))

    def test_add(self, space):
        w_res = space.execute("return 1.0 + 2.9")
        assert space.float_w(w_res) == 3.9

    def test_sub(self, space):
        w_res = space.execute("return 1.0 - 5.4")
        assert space.float_w(w_res) == -4.4

    def test_mul(self, space):
        w_res = space.execute("return 1.2 * 5.0")
        assert space.float_w(w_res) == 6.0

        w_res = space.execute("return 1.2 * 2")
        assert space.float_w(w_res) == 2.4

    def test_div(self, space):
        w_res = space.execute("return 5.0 / 2.0")
        assert space.float_w(w_res) == 2.5

    def test_neg(self, space):
        w_res = space.execute("return (-5.0)")
        assert space.float_w(w_res) == -5.0

        w_res = space.execute("return (-(4.0 + 1.0))")
        assert space.float_w(w_res) == -5.0

    def test_equal(self, space):
        w_res = space.execute("return 2.3 == 2.3")
        assert w_res is space.w_true
        w_res = space.execute("return 2.4 == 2.3")
        assert w_res is space.w_false

    def test_equal_method(self, space):
        w_res = space.execute("return 2.3.equal?(2.3)")
        assert w_res is space.w_true
        w_res = space.execute("return Float::NAN.equal?(Float::NAN)")
        assert w_res is space.w_true

    def test_hashability(self, space):
        w_res = space.execute("return 1.0.hash == 1.0.hash")
        assert w_res is space.w_true

    def test_to_s(self, space):
        w_res = space.execute("return 1.5.to_s")
        assert space.str_w(w_res) == "1.5"
        w_res = space.execute("return (0.0 / 0.0).to_s")
        assert space.str_w(w_res) == "NaN"
        w_res = space.execute("return (1.0 / 0.0).to_s")
        assert space.str_w(w_res) == "Infinity"
        w_res = space.execute("return (-1.0 / 0.0).to_s")
        assert space.str_w(w_res) == "-Infinity"

    def test_to_i(self, space):
        w_res = space.execute("return [1.1.to_i, 1.1.to_int]")
        assert self.unwrap(space, w_res) == [1, 1]
        with self.raises(space, "FloatDomainError", "NaN"):
            space.execute("(0.0 / 0.0).to_i")
        with self.raises(space, "FloatDomainError", "Infinity"):
            space.execute("(1.0 / 0.0).to_i")
        with self.raises(space, "FloatDomainError", "-Infinity"):
            space.execute("(-1.0 / 0.0).to_i")

    def test_lt(self, space):
        assert space.execute("return 1.1 < 1.2") is space.w_true
        assert space.execute("return 1.2 < 0") is space.w_false

    def test_lte(self, space):
        assert space.execute("return 1.1 <= 2") is space.w_true
        assert space.execute("return 1.0 <= 1") is space.w_true
        assert space.execute("return 1.1 <= 1.1") is space.w_true
        assert space.execute("return 1.1 <= 0.9") is space.w_false
        assert space.execute("return 1.0 <= '1.1'") is space.w_true
        with self.raises(space, "ArgumentError", "comparison of Float with String failed"):
            space.execute("1.0 <= 'a'")

    def test_gt(self, space):
        assert space.execute("return 1.1 > 1.2") is space.w_false
        assert space.execute("return 1.2 > 0") is space.w_true

    def test_gte(self, space):
        assert space.execute("return 1.1 >= 2") is space.w_false
        assert space.execute("return 1.0 >= 1") is space.w_true
        assert space.execute("return 1.1 >= 1.1") is space.w_true
        assert space.execute("return 1.1 >= 0.9") is space.w_true
        assert space.execute("return 1.0 >= '1.1'") is space.w_false
        with self.raises(space, "ArgumentError", "comparison of Float with String failed"):
            space.execute("1.0 >= 'a'")

    def test_abs(self, space):
        w_res = space.execute("return -123.534.abs")
        assert space.float_w(w_res) == 123.534

    def test_zero_division_nan(self, space):
        w_res = space.execute("return 0.0 / 0.0")
        assert math.isnan(self.unwrap(space, w_res))

    def test_zero_division_inf(self, space):
        w_res = space.execute("return 1.0 / 0.0")
        assert self.unwrap(space, w_res) == float('inf')
        w_res = space.execute("return -1.0 / 0.0")
        assert self.unwrap(space, w_res) == -float('inf')

    def test_pow(self, space):
        w_res = space.execute("return 1.0 ** 2")
        assert self.unwrap(space, w_res) == 1.0
        w_res = space.execute("return 2.0 ** 2")
        assert self.unwrap(space, w_res) == 4.0
        w_res = space.execute("return 2.0 ** 0")
        assert self.unwrap(space, w_res) == 1.0
        w_res = space.execute("return 4.0 ** 4.0")
        assert self.unwrap(space, w_res) == 256.0
        w_res = space.execute("return 0.0 ** (-1.0)")
        assert self.unwrap(space, w_res) == float('inf')
        w_res = space.execute("return (-2.0) ** 2")
        assert self.unwrap(space, w_res) == 4
        w_res = space.execute("return (-2.0) ** 3")
        assert self.unwrap(space, w_res) == -8
        w_res = space.execute("return (-2.0) ** -2")
        assert self.unwrap(space, w_res) == 0.25
        w_res = space.execute("return (-2.0) ** -3")
        assert self.unwrap(space, w_res) == -0.125
        with self.raises(space, "TypeError", "String can't be coerced into Bignum"):
            space.execute("18446744073709551628 ** 'hallo'")

    def test_pow_with_nan(self, space):
        w_res = space.execute("return (0.0 / 0.0) ** 1")
        assert math.isnan(self.unwrap(space, w_res))
        w_res = space.execute("return 1.0 ** (0.0 / 0.0)")
        assert self.unwrap(space, w_res) == 1.0
        w_res = space.execute("return 1.0 ** (0.0 / 0.0)")
        assert self.unwrap(space, w_res) == 1.0

    def test_pow_with_infinity(self, space):
        w_res = space.execute("return (1.0 / 0.0) ** 10")
        assert self.unwrap(space, w_res) == float('inf')
        w_res = space.execute("return (-1.0 / 0.0) ** 10")
        assert self.unwrap(space, w_res) == float('inf')
        w_res = space.execute("return (-1.0 / 0.0) ** 9")
        assert self.unwrap(space, w_res) == -float('inf')
        w_res = space.execute("return (-1.0 / 0.0) ** -10")
        assert self.unwrap(space, w_res) == 0.0
        w_res = space.execute("return (-1.0 / 0.0) ** -9")
        assert self.unwrap(space, w_res) == -0.0
        w_res = space.execute("return 1.0 ** (1.0 / 0.0)")
        assert self.unwrap(space, w_res) == 1.0
        w_res = space.execute("return (-1.0) ** (1.0 / 0.0)")
        assert self.unwrap(space, w_res) == -1.0
        w_res = space.execute("return 1.1 ** (1.0 / 0.0)")
        assert self.unwrap(space, w_res) == float('inf')
        w_res = space.execute("return (-1.1) ** (1.0 / 0.0)")
        assert self.unwrap(space, w_res) == float('inf')
        w_res = space.execute("return (-0.1) ** (1.0 / 0.0)")
        assert self.unwrap(space, w_res) == -0.0
        w_res = space.execute("return 0.1 ** (1.0 / 0.0)")
        assert self.unwrap(space, w_res) == 0.0
        w_res = space.execute("return 0.1 ** (-1.0 / 0.0)")
        assert self.unwrap(space, w_res) == float('inf')
        w_res = space.execute("return (-0.1) ** (-1.0 / 0.0)")
        assert self.unwrap(space, w_res) == float('inf')
        w_res = space.execute("return (-2) ** (-1.0 / 0.0)")
        assert self.unwrap(space, w_res) == 0.0
        w_res = space.execute("return 2 ** (-1.0 / 0.0)")
        assert self.unwrap(space, w_res) == 0.0

        w_res = space.execute("return 1 <=> 2")
        assert space.int_w(w_res) == -1

    def test_comparator_eq(self, space):
        w_res = space.execute("return 1.0 <=> 1.0")
        assert space.int_w(w_res) == 0

    def test_comparator_gt(self, space):
        w_res = space.execute("return 2.0 <=> 1.0")
        assert space.int_w(w_res) == 1

    def test_comparator_int(self, space):
        w_res = space.execute("return 1.1 <=> 1")
        assert space.int_w(w_res) == 1

    def test_comparator_other_type(self, space):
        w_res = space.execute("return 1.0 <=> '1'")
        assert w_res is space.w_nil

    def test_infinite(self, space):
        w_res = space.execute("return 1.0.infinite?")
        assert w_res is space.w_nil
        w_res = space.execute("return Float::INFINITY.infinite?")
        assert space.int_w(w_res) == 1
        w_res = space.execute("return (-Float::INFINITY).infinite?")
        assert space.int_w(w_res) == -1

    def test_nan(self, space):
        w_res = space.execute("return 1.0.nan?")
        assert w_res is space.w_false
        w_res = space.execute("return Float::NAN.nan?")
        assert w_res is space.w_true
