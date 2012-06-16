class TestHashObject(object):
    def test_create(self, ec):
        ec.space.execute(ec, "{2 => 3, 4 => 5}")

    def test_lookup(self, ec):
        w_res = ec.space.execute(ec, """
        x = {2 => 3}
        return x[2]
        """)
        assert self.unwrap(ec.space, w_res) == 3
