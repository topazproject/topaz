from rupypy.objects.intobject import W_FixnumObject

from ..base import BaseRuPyPyTest


class TestObjectObject(BaseRuPyPyTest):
    def test_class(self, space):
        w_res = space.execute("return 1.class")
        assert w_res is space.getclassfor(W_FixnumObject)

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
        assert self.unwrap(space, w_res) == [2, 3]

    def test_method_missing(self, space):
        w_res = space.execute("""
        class A
          def method_missing(name, *args, &block)
            return name, args, block
          end
        end
        return A.new.foo('bar', 42)
        """)
        assert self.unwrap(space, w_res) == ["foo", ["bar", 42], None]

class TestMapDict(BaseRuPyPyTest):
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
        assert self.unwrap(space, w_res) == [3, 4, 5]

    def test_unitialized_att(self, space):
        w_res = space.execute("""
        class X
            attr_accessor :a
            def attrs
                [self.a, @b]
            end
        end
        return X.new.attrs
        """)
        assert space.listview(w_res) == [space.w_nil, space.w_nil]
