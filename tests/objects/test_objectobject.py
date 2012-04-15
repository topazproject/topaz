from rupypy.objects.intobject import W_IntObject


class TestObjectObject(object):
    def test_class(self, space):
        w_res = space.execute("return 1.class")
        assert w_res is space.getclassobject(W_IntObject.classdef)

    def test_initialize(self, space):
        w_res = space.execute("""
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
        assert space.int_w(w_res) == 3

    def test_initialize_args(self, space):
        w_res = space.execute("""
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
        assert [space.int_w(w_x) for w_x in w_res.items_w] == [2, 3]

class TestMapDict(object):
    def test_simple_attr(self, space):
        w_res = space.execute("""
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
        assert [space.int_w(w_x) for w_x in w_res.items_w] == [3, 4, 5]