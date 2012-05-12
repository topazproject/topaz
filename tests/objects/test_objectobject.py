from rupypy.objects.intobject import W_IntObject


class TestObjectObject(object):
    def test_class(self, ec):
        w_res = ec.space.execute(ec, "return 1.class")
        assert w_res is ec.space.getclassfor(W_IntObject)

    def test_initialize(self, ec):
        w_res = ec.space.execute(ec, """
        class X
            def initialize
                @a = 3
            end

            def foo
                @a
            end
        end
        return X.new.foo
        """)
        assert ec.space.int_w(w_res) == 3

    def test_initialize_args(self, ec):
        w_res = ec.space.execute(ec, """
        class X
            def initialize a, b
                @a = a
                @b = b
            end
            def attrs
                [@a, @b]
            end
        end
        x = X.new 2, 3
        return x.attrs
        """)
        assert [ec.space.int_w(w_x) for w_x in ec.space.listview(w_res)] == [2, 3]


class TestMapDict(object):
    def test_simple_attr(self, ec):
        w_res = ec.space.execute(ec, """
        class X
            def initialize
                @a = 3
                @b = 4
                @c = 5
            end
            def attrs
                [@a, @b, @c]
            end
        end
        return X.new.attrs
        """)
        assert [ec.space.int_w(w_x) for w_x in ec.space.listview(w_res)] == [3, 4, 5]

    def test_unitialized_att(self, ec):
        w_res = ec.space.execute(ec, """
        class X
            attr_accessor :a
            def attrs
                [self.a, @b]
            end
        end
        return X.new.attrs
        """)
        assert ec.space.listview(w_res) == [ec.space.w_nil, ec.space.w_nil]
