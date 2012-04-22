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

        x = X.new(3)
        orig_a = x.a
        x.a = 5
        return [orig_a, x.a]
        """)
        assert [space.int_w(w_x) for w_x in w_res.items_w] == [3, 5]

    def test_attr_reader(self, space):
        w_res = space.execute("""
        class X
            attr_reader :a
            def initialize
                @a = 5
            end
        end
        return X.new.a
        """)
        assert space.int_w(w_res) == 5