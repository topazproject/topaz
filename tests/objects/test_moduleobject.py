from ..base import BaseRuPyPyTest


class TestModuleObject(BaseRuPyPyTest):
    def test_name(self, space):
        space.execute("Module")

    def test_new(self, space):
        w_res = space.execute("""
        m = Module.new
        m::Const = 4
        return m::Const
        """)
        assert space.int_w(w_res) == 4

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
          X.const_defined?("X"), Y.const_defined?("Const"), Y.const_defined?("Const", false),
          X.const_defined?("Const", false)
        """)
        assert self.unwrap(space, w_res) == [True, False, True, True, False, True]

    def test_const_get(self, space):
        space.execute("""
        class X
            Const = 1
        end
        class Y < X
        end
        """)
        w_res = space.execute("return X.const_get :Const")
        assert space.int_w(w_res) == 1
        w_res = space.execute("return Y.const_get :Const")
        assert space.int_w(w_res) == 1
        with self.raises(space, "NameError", "uninitialized constant Y::Const"):
            space.execute("Y.const_get :Const, false")

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

    def test_attr_writer(self, space):
        w_res = space.execute("""
        class X
          attr_writer :foo, :bar
          def ivars
            return @foo, @bar
          end
        end
        x = X.new
        x.foo = 1
        x.bar = 2
        return x.ivars
        """)
        assert self.unwrap(space, w_res) == [1, 2]

    def test_attr(self, space):
        space.execute("""
        class X
            attr :a, false
            attr :b, true
            attr :c, :d

            def set_a v
                @a = v
            end
        end
        """)
        with self.raises(space, "NoMethodError"):
            space.execute("X.new.a = 3")
        w_res = space.execute("""
        x = X.new
        x.set_a 3
        return x.a
        """)
        assert space.int_w(w_res) == 3

        w_res = space.execute("""
        x = X.new
        x.b = 5
        return x.b
        """)
        assert space.int_w(w_res) == 5

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

    def test_instance_method(self, space):
        w_res = space.execute("""
          class Interpreter
            def do_a() "there, "; end
            def do_d() "Hello ";  end
            def do_e() "!\n";     end
            def do_v() "Dave";    end
            Dispatcher = {
              "a" => instance_method(:do_a),
              "d" => instance_method(:do_d),
              "e" => instance_method(:do_e),
              "v" => instance_method(:do_v)
            }
            def interpret(instructions)
              instructions.map {|b| Dispatcher[b].bind(self).call }
            end
          end

          interpreter = Interpreter.new
          return interpreter.interpret(%w[d a v e])
        """)
        assert self.unwrap(space, w_res) == ["Hello ", "there, ", "Dave", "!\n"]

    def test_undef_method(self, space):
        space.execute("""
        class A
          def hello
          end
        end
        """)
        space.execute("""
        class A
          undef_method :hello
        end
        """)
        with self.raises(space, "NoMethodError", "undefined method `hello' for A"):
            space.execute("A.new.hello")
        with self.raises(space, "NameError", "undefined method `undefinedmethod' for class `A'"):
            space.execute("""
            class A
              undef_method :undefinedmethod
            end
            """)
        with self.raises(space, "NameError", "undefined method `hello' for class `A'"):
            space.execute("""
            class A
              undef_method :hello
            end
            """)
        space.execute("""
        class A
          undef_method :==
        end
        """)
        with self.raises(space, "NoMethodError", "undefined method `==' for A"):
            space.execute("""
            A.new == 1
            """)

    def test_remove_method(self, space):
        space.execute("""
        class A
            def foo
            end
        end
        """)
        space.execute("A.new.foo")
        space.execute("""
        class A
            remove_method :foo
        end
        """)
        with self.raises(space, "NoMethodError"):
            space.execute("A.new.foo")
        with self.raises(space, "NameError", "method `foo' not defined in A"):
            space.execute("""
            class A
                remove_method :foo
            end
            """)
        with self.raises(space, "NameError", "method `bar' not defined in A"):
            space.execute("""
            class A
                remove_method :bar
            end
            """)


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
