import py

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
        assert space.getclass(w_res) is w_cls

        w_res = space.execute("""
        class X
            def m
                self
            end
        end

        x = X.new
        return [x, x.m]
        """)

        [w_x, w_xm] = w_res.items_w
        assert w_xm is w_x

    def test_attr_accessor(self, space):
        w_res = space.execute("""
        class X
            attr_accessor :a
            def initialize a
                @a = a
            end
        end

        return X.new(3).a
        """)
        assert space.int_w(w_res) == 3

        py.test.skip("Needs attribute assignment")