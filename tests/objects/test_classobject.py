from rupypy.objects.objectobject import W_Object


class TestClassObject(object):
    def test_to_s(self, ec):
        w_res = ec.space.execute(ec, "return 1.class.to_s")
        assert ec.space.str_w(w_res) == "Fixnum"

        w_res = ec.space.execute(ec, "return 1.class.class.to_s")
        assert ec.space.str_w(w_res) == "Class"

    def test_new(self, ec):
        w_res = ec.space.execute(ec, """
        class X
        end

        return X.new
        """)
        w_cls = ec.space.getclassfor(W_Object).constants_w["X"]
        assert ec.space.getclass(w_res) is w_cls

        w_res = ec.space.execute(ec, """
        class X
            def m
                self
            end
        end

        x = X.new
        return [x, x.m]
        """)

        [w_x, w_xm] = ec.space.listview(w_res)
        assert w_xm is w_x

    def test_attr_accessor(self, ec):
        w_res = ec.space.execute(ec, """
        class X
            attr_accessor :a, :b, :c
            def initialize a
                @a = a
                self.b = 25
            end
        end

        x = X.new(3)
        orig_a = x.a
        x.a = 5
        return [orig_a, x.a, x.b]
        """)
        assert [ec.space.int_w(w_x) for w_x in ec.space.listview(w_res)] == [3, 5, 25]

    def test_attr_reader(self, ec):
        w_res = ec.space.execute(ec, """
        class X
            attr_reader :a
            def initialize
                @a = 5
            end
        end
        return X.new.a
        """)
        assert ec.space.int_w(w_res) == 5
