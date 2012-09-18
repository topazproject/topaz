from rupypy.objects.intobject import W_FixnumObject

from ..base import BaseRuPyPyTest


class TestBaseObject(BaseRuPyPyTest):
    def test_instance_eval(self, space):
        w_res = space.execute("""
        class X; end
        X.instance_eval('def foo; 1; end')
        return X.foo
        """)
        assert space.int_w(w_res) == 1

        w_res = space.execute("""
        class X; end
        X.instance_eval { def foo; 1; end }
        return X.foo
        """)
        assert space.int_w(w_res) == 1

        w_res = space.execute("""
        class X; end
        X.instance_eval('def foo; [__FILE__, __LINE__]; end', 'dummy', 123)
        return X.foo
        """)
        assert self.unwrap(space, w_res) == ["dummy", 123]

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

    def test_instance_variable_get(self, space):
        w_res = space.execute("""
        class Fred
          def initialize(p1, p2)
            @a, @b = p1, p2
          end
        end
        fred = Fred.new('cat', 99)
        return fred.instance_variable_get(:@a), fred.instance_variable_get("@b")
        """)
        assert self.unwrap(space, w_res) == ["cat", 99]

    def test_instance_variable_set(self, space):
        w_res = space.execute("""
        class A
          def foo; @foo; end
        end
        a = A.new
        a.instance_variable_set(:@foo, "bar")
        return a.foo
        """)
        assert space.str_w(w_res) == "bar"

    def test_to_s(self, space):
        w_res = space.execute("""
        obj = Object.new
        return obj.to_s, obj.object_id
        """)
        s, oid = self.unwrap(space, w_res)
        assert s == "#<Object:0x%x>" % oid

    def test_send(self, space):
        w_res = space.execute("return [1.send(:to_s), 1.send('+', 2)]")
        assert self.unwrap(space, w_res) == ['1', 3]

    def test_eqeqeq(self, space):
        w_res = space.execute("""
        class A; end
        a = A.new
        res = [a === A.new]
        class A; def ==(o); true; end; end
        res << (a === A.new)
        return res
        """)
        assert self.unwrap(space, w_res) == [False, True]

    def test_hash(self, space):
        w_res = space.execute("""
        a = Object.new
        return a.hash, a.hash == a.hash, a.hash != Object.new.hash
        """)
        w_int, w_self_hash, w_other_hash = space.listview(w_res)
        assert isinstance(w_int, W_FixnumObject)
        assert w_self_hash is space.w_true
        assert w_other_hash is space.w_true

    def test_is_kind_ofp(self, space):
        w_res = space.execute("""
        r = []
        module M; end
        class A
          include M
        end
        class B < A; end
        class C < B; end
        b = B.new
        r << b.kind_of? A
        r << b.kind_of? B
        r << b.kind_of? C
        r << b.kind_of? M
        return r
        """)
        assert self.unwrap(space, w_res) == [True, True, False, True]


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
