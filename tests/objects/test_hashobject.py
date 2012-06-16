class TestHashObject(object):
    def test_create(self, space):
        space.execute("{2 => 3, 4 => 5}")

    def test_lookup(self, space):
        w_res = space.execute("""
        x = {2 => 3}
        return x[2]
        """)
        assert self.unwrap(space, w_res) == 3
