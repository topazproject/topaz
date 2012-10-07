class TestNilObject(object):
    def test_name(self, space):
        space.execute("NilClass")

    def test_to_s(self, space):
        w_res = space.execute("return nil.to_s")
        assert space.str_w(w_res) == ""

    def test_nilp(self, space):
        w_res = space.execute("return nil.nil?")
        assert w_res == space.w_true
        w_res = space.execute("return 1.nil?")
        assert w_res == space.w_false

    def test_to_i(self, space):
        w_res = space.execute("return nil.to_i")
        assert space.int_w(w_res) == 0
