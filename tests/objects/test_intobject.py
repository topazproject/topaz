import math
import sys

from rpython.rlib.rarithmetic import LONG_BIT
from rpython.rlib.rbigint import rbigint

from ..base import BaseTopazTest


class TestFixnumObject(BaseTopazTest):
    def test_addition(self, space):
        w_res = space.execute("return 1 + 2")
        assert space.int_w(w_res) == 3

        w_res = space.execute("return 1 + 2.5")
        assert space.float_w(w_res) == 3.5

    def test_addition_ovf(self, space):
        w_res = space.execute("return (2 << (0.size * 8 - 3)) + (2 << (0.size * 8 - 3)) + (2 << (0.size * 8 - 3))")
        assert space.bigint_w(w_res) == rbigint.fromlong((2 << (LONG_BIT - 3)) * 3)

    def test_addition_bigint(self, space):
        w_res = space.execute("return 2 + %d" % (sys.maxint + 1))
        assert self.unwrap(space, w_res) == rbigint.fromlong(sys.maxint + 3)

    def test_multiplication(self, space):
        w_res = space.execute("return 2 * 3")
        assert space.int_w(w_res) == 6

    def test_multiplication_ovf(self, space):
        w_res = space.execute("return (2 << (0.size * 8 - 3)) * (2 << (0.size * 8 - 3))")
        assert space.bigint_w(w_res) == rbigint.fromlong((2 << (LONG_BIT - 3)) ** 2)

    def test_multiplication_bigint(self, space):
        w_res = space.execute("return 1 * %d" % (sys.maxint + 1))
        assert self.unwrap(space, w_res) == rbigint.fromlong(sys.maxint + 1)

    def test_subtraction(self, space):
        w_res = space.execute("return 2 - 3")
        assert space.int_w(w_res) == -1

        w_res = space.execute("return 2 - 3.5")
        assert space.float_w(w_res) == -1.5

    def test_subtraction_ovf(self, space):
        w_res = space.execute("return 0 - (2 << (0.size * 8 - 3)) - (2 << (0.size * 8 - 3)) - (2 << (0.size * 8 - 3))")
        assert space.bigint_w(w_res) == rbigint.fromlong((2 << (LONG_BIT - 3)) * -3)

    def test_substraction_bigint(self, space):
        w_res = space.execute("return 1 - %d" % (sys.maxint + 1))
        assert self.unwrap(space, w_res) == rbigint.fromlong(1 - sys.maxint - 1)

    def test_division(self, space):
        w_res = space.execute("return 3 / 5")
        assert space.int_w(w_res) == 0
        w_res = space.execute("return 3 / 5.0")
        assert space.float_w(w_res) == 0.6
        w_res = space.execute("return 3 / (0.0 / 0.0)")
        assert math.isnan(space.float_w(w_res))
        w_res = space.execute("return 3 / (1.0 / 0.0)")
        assert space.float_w(w_res) == 0.0
        w_res = space.execute("return 3 / (1.0 / -0.0)")
        assert space.float_w(w_res) == -0.0

    def test_div(self, space):
        w_res = space.execute("return 3.div(5)")
        assert space.int_w(w_res) == 0
        w_res = space.execute("return 3.div(5.0)")
        assert space.int_w(w_res) == 0
        with self.raises(space, "ZeroDivisionError", "divided by 0"):
            space.execute("return 3.div(0)")
        with self.raises(space, "FloatDomainError", "NaN"):
            space.execute("return 3.div(0.0 / 0.0)")

    def test_modulo(self, space):
        w_res = space.execute("return 5 % 2")
        assert space.int_w(w_res) == 1

    def test_left_shift(self, space):
        w_res = space.execute("return 3 << 4")
        assert space.int_w(w_res) == 48
        w_res = space.execute("return 48 << -4")
        assert space.int_w(w_res) == 3

    def test_left_shift_ovf(self, space):
        w_res = space.execute("return 4 << 90")
        assert space.bigint_w(w_res) == rbigint.fromlong(4951760157141521099596496896)
        w_res = space.execute("return %d << 2" % sys.maxint)
        assert self.unwrap(space, w_res) == rbigint.fromlong(sys.maxint << 2)
        w_res = space.execute("return 4 << -90")
        assert space.int_w(w_res) == 0

    def test_and(self, space):
        w_res = space.execute("return 12 & 123")
        assert space.int_w(w_res) == 8

    def test_xor(self, space):
        w_res = space.execute("return 12 ^ 15")
        assert space.int_w(w_res) == 3

    def test_or(self, space):
        w_res = space.execute("return 16 | 7")
        assert space.int_w(w_res) == 23
        w_res = space.execute("return 7 | 3")
        assert space.int_w(w_res) == 7

    def test_equal(self, space):
        w_res = space.execute("return 1 == 1")
        assert w_res is space.w_true
        w_res = space.execute("""
        class A
          def ==(o); 'hi'; end
        end
        return 1 == A.new
        """)
        assert space.str_w(w_res) == 'hi'
        w_res = space.execute("return 1 == '1'")
        assert w_res is space.w_false

    def test_not_equal(self, space):
        w_res = space.execute("return 1 != 1")
        assert w_res is space.w_false
        w_res = space.execute("return 1 != '1'")
        assert w_res is space.w_true
        w_res = space.execute("""
        class A
          def ==(o); 'hi'; end
        end
        return 1 != A.new
        """)
        assert w_res is space.w_false

    def test_less(self, space):
        w_res = space.execute("return 1 < 2")
        assert w_res is space.w_true
        w_res = space.execute("return 1 < 1.2")
        assert w_res is space.w_true

    def test_less_equal(self, space):
        assert space.execute("return 1 <= 2") is space.w_true
        assert space.execute("return 1 <= 1") is space.w_true
        assert space.execute("return 1 <= 1.1") is space.w_true
        assert space.execute("return 1 <= 0.9") is space.w_false
        assert space.execute("return 1 <= '1.1'") is space.w_true
        with self.raises(space, "ArgumentError", "comparison of Fixnum with String failed"):
            space.execute("1 <= 'a'")

    def test_greater(self, space):
        w_res = space.execute("return 1 > 2")
        assert w_res is space.w_false

    def test_greater_equal(self, space):
        w_res = space.execute("return 5 >= 4")
        assert w_res is space.w_true

    def test_times(self, space):
        w_res = space.execute("""
        res = []
        3.times do |x|
          res << x
        end
        return res
        """)
        assert self.unwrap(space, w_res) == [0, 1, 2]

    def test_upto(self, space):
        w_res = space.execute("""
        res = []
        3.upto(6) do |x|
          res << x
        end
        return res
        """)
        assert self.unwrap(space, w_res) == [3, 4, 5, 6]

    def test_comparator_lt(self, space):
        w_res = space.execute("return 1 <=> 2")
        assert space.int_w(w_res) == -1

    def test_comparator_eq(self, space):
        w_res = space.execute("return 1 <=> 1")
        assert space.int_w(w_res) == 0

    def test_comparator_gt(self, space):
        w_res = space.execute("return 2 <=> 1")
        assert space.int_w(w_res) == 1

    def test_comparator_float(self, space):
        w_res = space.execute("return 1 <=> 1.1")
        assert space.int_w(w_res) == -1

    def test_comparator_other_type(self, space):
        w_res = space.execute("return 1 <=> '1'")
        assert w_res is space.w_nil

    def test_eqlp(self, space):
        w_res = space.execute("return 1.eql? 1.0")
        assert w_res is space.w_false
        w_res = space.execute("return 1.eql? 1")
        assert w_res is space.w_true

    def test_to_i(self, space):
        w_res = space.execute("return [1.to_i, 1.to_int]")
        assert self.unwrap(space, w_res) == [1, 1]

    def test_nonzero(self, space):
        w_res = space.execute("return [2.nonzero?, 0.nonzero?]")
        assert self.unwrap(space, w_res) == [2, None]

    def test_object_id(self, space):
        w_res = space.execute("return 2.object_id, 2.object_id")
        id_1, id_2 = self.unwrap(space, w_res)
        assert id_1 == id_2

    def test___id__(self, space):
        w_res = space.execute("return 2.__id__, 2.__id__")
        id_1, id_2 = self.unwrap(space, w_res)
        assert id_1 == id_2

    def test_ivar(self, space):
        w_res = space.execute("""
        class Fixnum
          def set; @foo = -1; end
          def get; @foo; end
        end
        2.set
        return 2.get, 2.get, 3.get
        """)
        [x, y, z] = self.unwrap(space, w_res)
        assert x == y == -1
        assert z is None

    def test_freeze(self, space):
        w_res = space.execute("""
        res = [1.frozen?]
        1.freeze
        res << 1.frozen?
        res << 2.frozen?
        return res
        """)
        assert self.unwrap(space, w_res) == [False, True, False]

    def test_succ(self, space):
        w_res = space.execute("return -1.succ")
        assert self.unwrap(space, w_res) == 0

        w_res = space.execute("return 7.succ")
        assert self.unwrap(space, w_res) == 8

    def test_zero(self, space):
        w_res = space.execute("return [0.zero?, 2.zero?]")
        assert self.unwrap(space, w_res) == [True, False]

    def test_even(self, space):
        w_res = space.execute("return [1.even?, -2.even?]")
        assert self.unwrap(space, w_res) == [False, True]

    def test_odd(self, space):
        w_res = space.execute("return [2.odd?, -1.odd?]")
        assert self.unwrap(space, w_res) == [False, True]

    def test_size(self, space):
        if sys.maxint == 2 ** 63 - 1:
            expected = 8
        elif sys.maxint == 2 ** 31 - 1:
            expected = 4
        else:
            raise NotImplementedError(sys.maxint)
        w_res = space.execute("return 1.size")
        assert space.int_w(w_res) == expected

    def test_chr(self, space):
        w_res = space.execute("return 65.chr")
        assert self.unwrap(space, w_res) == "A"
        with self.raises(space, "RangeError", "256 out of char range"):
            space.execute("256.chr")
        with self.raises(space, "RangeError", "-1 out of char range"):
            space.execute("-1.chr")
        w_res = space.execute("return 4.chr")
        assert self.unwrap(space, w_res) == "\x04"

    def test_pow(self, space):
        w_res = space.execute("return 2 ** 6")
        assert self.unwrap(space, w_res) == 64
        w_res = space.execute("return 2 ** -6")
        assert self.unwrap(space, w_res) == 1.0 / 64
        w_res = space.execute("return 4 ** 0.5")
        assert self.unwrap(space, w_res) == 2.0
        w_res = space.execute("return 4 ** -0.5")
        assert self.unwrap(space, w_res) == 0.5
        with self.raises(space, "TypeError", "String can't be coerced into Fixnum"):
            space.execute("2 ** 'hallo'")

    def test_step(self, space):
        w_res = space.execute("""
        res = []
        1.step(4) { |i| res << i }
        return res
        """)
        assert self.unwrap(space, w_res) == [1, 2, 3, 4]
        w_res = space.execute("""
        res = []
        1.step(4.1) { |i| res << i }
        return res
        """)
        assert self.unwrap(space, w_res) == [1.0, 2.0, 3.0, 4.0]
        w_res = space.execute("""
        res = []
        1.step(10, 2) { |i| res << i }
        return res
        """)
        assert self.unwrap(space, w_res) == [1, 3, 5, 7, 9]
        w_res = space.execute("""
        res = []
        1.step(2, 0.6) { |i| res << i }
        return res
        """)
        assert self.unwrap(space, w_res) == [1.0, 1.6]
