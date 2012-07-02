from rupypy.objects.intobject import W_FixnumObject

from ..base import BaseRuPyPyTest


class TestBasicObject(BaseRuPyPyTest):
    def test___id__(self, space):
        w_res = space.execute("return BasicObject.new.__id__")
        assert isinstance(w_res, W_FixnumObject)

    def test_method_missing(self, space):
        w_res = space.execute("""
        class BasicObject
          def method_missing(name, *args, &block)
            return name, args, block
          end
        end
        return BasicObject.new.foo('bar', 42)
        """)
        assert self.unwrap(space, w_res) == ["foo", ["bar", 42], None]

    def test_eq(self, space):
        w_res = space.execute("""
        a = BasicObject.new
        return [a == a, a == BasicObject.new]
        """)
        assert self.unwrap(space, w_res) == [True, False]
        w_res = space.execute("""
        a = BasicObject.new
        return [a.equal?(a), a.equal?(BasicObject.new)]
        """)
        assert self.unwrap(space, w_res) == [True, False]

    def test_neq(self, space):
        w_res = space.execute("""
        a = BasicObject.new
        return [a != a, a != BasicObject.new]
        """)
        assert self.unwrap(space, w_res) == [False, True]

    def test_not(self, space):
        w_res = space.execute("return !BasicObject.new")
        assert w_res is space.w_false
        w_res = space.execute("return !true")
        assert w_res is space.w_false
        w_res = space.execute("return !false")
        assert w_res is space.w_true
        w_res = space.execute("return !nil")
        assert w_res is space.w_true

    def test___send__(self, space):
        w_res = space.execute("""
        return [BasicObject.new.__send__("!"), BasicObject.new.__send__(:"==", BasicObject.new)]
        """)
        assert self.unwrap(space, w_res) == [False, False]


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

    def test_to_s(self, space):
        w_res = space.execute("""
        obj = Object.new
        return obj.to_s, obj.object_id
        """)
        s, oid = self.unwrap(space, w_res)
        assert s == "#<Object:0x%x>" % oid

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
