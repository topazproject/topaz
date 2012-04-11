class TestObjectObject(object):
    def test_class(self, space):
        w_res = space.execute("return 1.class.to_s")
        assert space.str_w(w_res) == "Fixnum"