from pypy.rlib.rbigint import rbigint


class TestBignumObject(object):
    def test_plus(self, space):
        w_res = space.execute("return 18446744073709551628 + 9")
        assert space.bigint_w(w_res) == rbigint.fromlong(18446744073709551637)

    def test_neg(self, space):
        w_res = space.execute("return -(18446744073709551628)")
        assert space.bigint_w(w_res) == rbigint.fromlong(-18446744073709551628)
