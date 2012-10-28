class TestNilObject(object):
    def test_name(self, space):
        space.execute("NilClass")

    def test_to_s(self, space):
        w_res = space.execute("return nil.to_s")
        assert space.str_w(w_res) == ""

    def test_inspect(self, space):
        w_res = space.execute("return nil.inspect")
        assert space.str_w(w_res) == "nil"

    def test_nilp(self, space):
        w_res = space.execute("return nil.nil?")
        assert w_res == space.w_true
        w_res = space.execute("return 1.nil?")
        assert w_res == space.w_false

    def test_to_i(self, space):
        w_res = space.execute("return nil.to_i")
        assert space.int_w(w_res) == 0

    def test_singleton_class(self, space):
        w_res = space.execute("return nil.singleton_class == NilClass")
        assert w_res is space.w_true
