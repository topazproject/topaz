import pytest
from ..base import BaseTopazTest


class TestClassObject(BaseTopazTest):
    def test_name(self, space):
        space.execute("Class")

    def test_generated_subclass(self, space):
        w_res = space.execute("""
        class Foo
          class Bar
            class Baz
            end
          end
        end
        return Foo::Bar::Baz.name
        """)
        assert space.str_w(w_res) == "Foo::Bar::Baz"

    def test_to_s(self, space):
        w_res = space.execute("return 1.class.to_s")
        assert space.str_w(w_res) == "Fixnum"

        w_res = space.execute("return 1.class.class.to_s")
        assert space.str_w(w_res) == "Class"

    def test_anon_class_to_s(self, space):
        w_res = space.execute("return Class.new.to_s")
        assert space.str_w(w_res).startswith("#<Class:0x")

        w_res = space.execute("return Class.new.new.to_s")
        assert space.str_w(w_res).startswith("#<#<Class:0x")

    @pytest.mark.xfail
    def test_singletonclass_to_s(self, space):
        w_res = space.execute("Class.new.singleton_class.to_s")
        assert space.str_w(w_res).startswith("#<Class:#<Class:0x")

    def test_anon_class_name(self, space):
        w_res = space.execute("return Class.new.name")
        assert w_res is space.w_nil

    def test_anon_class_method_missing_raises(self, space):
        with self.raises(space, "NoMethodError"):
            space.execute("""
            class A; end
            Class.new.does_not_exist
            """)

    def test_singletonclass_name(self, space):
        w_res = space.execute("Class.new.singleton_class.name")
        assert w_res is space.w_nil

    def test_class_new(self, space):
        w_res = space.execute("return Class.new.superclass.name")
        assert space.str_w(w_res) == "Object"
        w_res = space.execute("return Class.new(String).superclass.name")
        assert space.str_w(w_res) == "String"

    def test_new(self, space):
        w_res = space.execute("""
        class X
        end

        return X.new
        """)
        w_cls = space.w_object.constants_w["X"]
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

        [w_x, w_xm] = space.listview(w_res)
        assert w_xm is w_x

    def test_superclass(self, space):
        w_res = space.execute("return Object.superclass")
        assert w_res is space.w_basicobject
        w_res = space.execute("return BasicObject.superclass")
        assert w_res is space.w_nil

    def test_attr_accessor(self, space):
        w_res = space.execute("""
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
        assert [space.int_w(w_x) for w_x in space.listview(w_res)] == [3, 5, 25]

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
