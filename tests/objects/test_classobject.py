from rupypy.objects.objectobject import W_Object


class TestClassObject(object):
    def test_to_s(self, space):
        w_res = space.execute("return 1.class.to_s")
        assert space.str_w(w_res) == "Fixnum"

        w_res = space.execute("return 1.class.class.to_s")
        assert space.str_w(w_res) == "Class"

    def test_new(self, space):
        w_res = space.execute("""
        class X
        end

        return X.new
        """)
        w_cls = space.getclassfor(W_Object).constants_w["X"]
        assert w_res.klass is w_cls