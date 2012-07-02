class TestNilObject(object):
    def test_to_s(self, space):
        w_res = space.execute("return nil.to_s")
        assert space.str_w(w_res) == ""
