from ..base import BaseRuPyPyTest


class TestModuleObject(BaseRuPyPyTest):
    def test_module_function(self, space):
        w_res = space.execute("""
        module Mod
            def f
                3
            end
            module_function :f
        end
        class X
            include Mod
            def meth
                f + 2
            end
        end
        return [Mod.f, X.new.meth]
        """)
        assert self.unwrap(space, w_res) == [3, 5]

    def test_alias_method(self, space):
        w_res = space.execute("""
        class X
            def f
                3
            end
            alias_method :g, :f
        end

        return X.new.g
        """)
        assert self.unwrap(space, w_res) == 3

    def test_singleton_class(self, space):
        w_res = space.execute("""
        class X; end
        return X.singleton_class, X.singleton_class.ancestors, X.singleton_class.class
        """)
        s, s_ancs, s_class = self.unwrap(space, w_res)
        assert s not in s_ancs
        assert s_class == s_ancs[0]

        w_res = space.execute("""
        class X; end
        return X.singleton_class, X.singleton_class.singleton_class
        """)
        s, s_s = self.unwrap(space, w_res)
        assert s.name == "#<Class:X>"
        assert s_s.name == "#<Class:#<Class:X>>"

    def test_instance_variable(self, space):
        w_res = space.execute("""
        class X
            @abc = 3
            def self.m
                @abc
            end
        end

        return X.m
        """)
        assert self.unwrap(space, w_res) == 3

    def test_missing_instance_variable(self, space):
        w_res = space.execute("""
        class X
            def self.m
                @a
            end
        end
        return X.m
        """)
        assert self.unwrap(space, w_res) is None

    def test_module_eval(self, space, capfd):
        w_res = space.execute("""
        class X; end
        X.module_eval('def foo; 1; end')
        return X.new.foo
        """)
        assert space.int_w(w_res) == 1

        w_res = space.execute("""
        class X; end
        X.module_eval { def foo; 1; end }
        return X.new.foo
        """)
        assert space.int_w(w_res) == 1

        w_res = space.execute("""
        class X; end
        X.module_eval('def foo; [__FILE__, __LINE__]; end', 'dummy', 123)
        return X.new.foo
        """)
        assert self.unwrap(space, w_res) == ["dummy", 123]

    def test_const_definedp(self, space):
        w_res = space.execute("""
        class X; Const = 1; end
        class Y < X; end
        return X.const_defined?("Const"), X.const_defined?("NoConst"),
          X.const_defined?("X"), Y.const_defined?("Const"), Y.const_defined?("Const", false)
        """)
        assert self.unwrap(space, w_res) == [True, False, True, True, False]

    def test_method_definedp(self, space):
        w_res = space.execute("""
        class X; def foo; end; end
        return X.method_defined?("foo"), X.method_defined?("no_method")
        """)
        assert self.unwrap(space, w_res) == [True, False]

    def test_attr_reader(self, space):
        w_res = space.execute("""
        class X
          attr_reader :foo, :bar
          def initialize; @foo = 1; @bar = 2; end
        end
        return X.new.foo, X.new.bar
        """)
        assert self.unwrap(space, w_res) == [1, 2]

    def test_attr_accessor(self, space):
        w_res = space.execute("""
        class X; attr_accessor :foo, :bar; end
        x = X.new
        x.foo = 1
        x.bar = 2
        return x.foo, x.bar
        """)
        assert self.unwrap(space, w_res) == [1, 2]

    def test_eqeqeq(self, space):
        w_res = space.execute("""
        r = []
        module M; end
        class A
          include M
        end
        class B < A; end
        class C < B; end
        b = B.new
        r << (A === b)
        r << (B === b)
        r << (C === b)
        r << (M === b)
        return r
        """)
        assert self.unwrap(space, w_res) == [True, True, False, True]


class TestMethodVisibility(object):
    def test_private(self, space):
        space.execute("""
        class X
            def m
            end
            private :m
        end
        """)

    def test_public(self, space):
        space.execute("""
        class X
            def m
            end
            public :m
        end
        """)

    def test_protected(self, space):
        space.execute("""
        class X
            protected
        end
        """)

    def test_private_class_method(self, space):
        space.execute("""
        class X
            def m
            end
            private_class_method :m
        end
        """)

    def test_public_class_method(self, space):
        space.execute("""
        class X
            def m
            end
            public_class_method :m
        end
        """)
