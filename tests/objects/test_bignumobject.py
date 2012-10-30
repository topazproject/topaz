from pypy.rlib.rbigint import rbigint


class TestBignumObject(object):
    def test_plus(self, space):
        w_res = space.execute("return 18446744073709551628 + 9")
        assert space.bigint_w(w_res) == rbigint.fromlong(18446744073709551637)

    def test_sub(self, space):
        w_res = space.execute("return 18446744073709551628 - 18446744073709551658")
        assert space.bigint_w(w_res) == rbigint.fromint(-30)

    def test_neg(self, space):
        w_res = space.execute("return -(18446744073709551628)")
        assert space.bigint_w(w_res) == rbigint.fromlong(-18446744073709551628)

    def test_and(self, space):
        w_res = space.execute("return 18446744073709551628 & 18446744073709551658")
        assert space.bigint_w(w_res) == rbigint.fromlong(18446744073709551624)

    def test_xor(self, space):
        w_res = space.execute("return 18446744073709551628 ^ 18446744073709551658")
        assert space.bigint_w(w_res) == rbigint.fromint(38)

    def test_eq(self, space):
        w_res = space.execute("return 18446744073709551628 == 18446744073709551628")
        assert w_res is space.w_true
        w_res = space.execute("return 18446744073709551628 == 18446744073709551629")
        assert w_res is space.w_false

    def test_hash(self, space):
        w_res = space.execute("return 18446744073709551628.hash == 18446744073709551628.hash")
        assert w_res is space.w_true
        w_res = space.execute("return 18446744073709551628.hash == 18446744073709551658.hash")
        assert w_res is space.w_false
