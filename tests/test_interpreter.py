import math

from topaz.objects.moduleobject import W_ModuleObject

from .base import BaseTopazTest


class TestInterpreter(BaseTopazTest):
    def test_add(self, space):
        space.execute("1 + 1")

    def test_global_send(self, space, capfd):
        space.execute("puts 1")
        out, err = capfd.readouterr()
        assert out == "1\n"
        assert not err

    def test_obj_send(self, space):
        w_res = space.execute("return 1.to_s")
        assert space.str_w(w_res) == "1"

    def test_variables(self, space):
        w_res = space.execute("a = 100; return a")
        assert space.int_w(w_res) == 100

    def test_uninitailized_variables(self, space):
        w_res = space.execute("""
        if false
          x = 5
        end
        return x
        """)
        assert w_res is space.w_nil

    def test_uninitialized_closure_var(self, space):
        w_res = space.execute("""
        if false
          x = 3
        end
        proc { x }
        return x
        """)
        assert w_res is space.w_nil

    def test_if(self, space):
        w_res = space.execute("if 3 then return 2 end")
        assert space.int_w(w_res) == 2

        w_res = space.execute("x = if 3 then 5 end; return x")
        assert space.int_w(w_res) == 5

        w_res = space.execute("x = if false then 5 end; return x")
        assert w_res is space.w_nil

        w_res = space.execute("x = if nil then 5 end; return x")
        assert w_res is space.w_nil

        w_res = space.execute("x = if 3 then end; return x")
        assert w_res is space.w_nil

    def test_while(self, space):
        w_res = space.execute("""
        i = 0
        while i < 1
          i += 1
        end
        return i
        """)
        assert space.int_w(w_res) == 1

        w_res = space.execute("""
        x = while false do end
        return x
        """)
        assert w_res is space.w_nil

    def test_for_loop(self, space):
        w_res = space.execute("""
        i = 0
        for i, *rest, b in [1, 2, 3] do
          bbb = "hello"
        end
        return i, bbb, rest, b
        """)
        assert self.unwrap(space, w_res) == [3, "hello", [], None]

        w_res = space.execute("""
        i = 0
        for i, *rest, b in [[1, 2, 3, 4]] do
          bbb = "hello"
        end
        return i, bbb, rest, b
        """)
        assert self.unwrap(space, w_res) == [1, "hello", [2, 3], 4]

        w_res = space.execute("""
        for i, *$c, @a in [[1, 2, 3, 4]] do
          bbb = "hello"
        end
        return i, bbb, $c, @a
        """)
        assert self.unwrap(space, w_res) == [1, "hello", [2, 3], 4]

        with self.raises(space, "NoMethodError", "undefined method `each' for Fixnum"):
            space.execute("for i in 1; end")

        w_res = space.execute("""
        class A
          def each
            [1, 2, 3]
          end
        end
        for i in A.new; end
        return i
        """)
        assert self.unwrap(space, w_res) is None

        w_res = space.execute("""
        a = []
        i = 0
        for a[i], i in [[1, 1], [2, 2]]; end
        return a, i
        """)
        assert self.unwrap(space, w_res) == [[1, 2], 2]

        w_res = space.execute("""
        for i in [[1, 1]]; end
        for j, in [[1, 1]]; end
        return i, j
        """)
        assert self.unwrap(space, w_res) == [[1, 1], 1]

        w_res = space.execute("""
        i = 15
        for i in []; end
        return i
        """)
        assert self.unwrap(space, w_res) == 15

        w_res = space.execute("""
        for a.bar in []; end
        return defined?(a)
        """)
        assert self.unwrap(space, w_res) is None

        w_res = space.execute("""
        for a.bar in []; end
        for b[i] in []; end
        return defined?(a), defined?(b), defined?(i)
        """)
        assert self.unwrap(space, w_res) == [None, None, None]

    def test_return(self, space):
        w_res = space.execute("return 4")
        assert space.int_w(w_res) == 4

    def test_array(self, space):
        w_res = space.execute("return [[1], [2], [3]]")
        assert self.unwrap(space, w_res) == [[1], [2], [3]]

    def test_def_function(self, space):
        w_res = space.execute("return def f() end")
        assert w_res is space.w_nil

        w_res = space.execute("""
        def f(a, b)
          a + b
        end
        return f 1, 2
        """)
        assert space.int_w(w_res) == 3
        w_res = space.execute("return Object.f(5, -2)")
        assert space.int_w(w_res) == 3

    def test_splat_first_in_def_function(self, space):
        w_res = space.execute("""
        def self.f(*a, b, c, &blk)
          a << b << c << blk.call
        end
        return f(2, 3, 'b', 'c') do
          "blk"
        end
        """)
        assert self.unwrap(space, w_res) == [2, 3, 'b', 'c', 'blk']

        w_res = space.execute("""
        def f(*a, b, c, &blk)
          a << b << c << blk.call
        end
        return f(2, 3, 'b', 'c') do
          "blk"
        end
        """)
        assert self.unwrap(space, w_res) == [2, 3, 'b', 'c', 'blk']

    def test_interpreter(self, space):
        w_res = space.execute('return "abc"')
        assert space.str_w(w_res) == "abc"

        w_res = space.execute("""
        def test
          x = ""
          x << "abc"
        end

        return [test, test]
        """)
        assert self.unwrap(space, w_res) == ["abc", "abc"]

    def test_class(self, space):
        w_res = space.execute("""
        class X
          def m
            self
          end

          def f
            2
          end
        end
        """)
        w_cls = space.w_object.constants_w["X"]
        assert w_cls.methods_w.viewkeys() == {"m", "f"}

        w_res = space.execute("""
        class Z < X
          def g
            3
          end
        end

        z = Z.new
        return [z.f, z.g]
        """)
        assert self.unwrap(space, w_res) == [2, 3]

    def test_reopen_class(self, space):
        space.execute("""
        class X
          def f
            3
          end
        end

        class X
          def m
            5
          end
        end
        """)
        w_cls = space.w_object.constants_w["X"]
        assert w_cls.methods_w.viewkeys() == {"m", "f"}

    def test_reopen_non_class(self, space):
        space.execute("""
        X = 12
        """)
        with self.raises(space, "TypeError", "X is not a class"):
            space.execute("""
            class X
            end
            """)

    def test_attach_class_non_module(self, space):
        with self.raises(space, "TypeError", "nil is not a class/module"):
            space.execute("""
            class nil::Foo
            end
            """)

    def test_shadow_class(self, space):
        w_res = space.execute("""
        class X; class Y; end; end

        class A < X
          OLD_Y = Y
          class Y; end
        end
        return A::OLD_Y.object_id == A::Y.object_id, A::OLD_Y.object_id == X::Y.object_id
        """)
        assert self.unwrap(space, w_res) == [False, True]

    def test_class_returnvalue(self, space):
        w_res = space.execute("""
        return (class X
          5
        end)
        """)
        assert space.int_w(w_res) == 5

    def test_singleton_class(self, space):
        w_res = space.execute("""
        class X
          def initialize
            @a = 3
          end
        end

        x = X.new
        class << x
          def m
            6
          end
        end
        return x.m
        """)
        assert space.int_w(w_res) == 6

        with self.raises(space, "NoMethodError"):
            space.execute("X.new.m")

    def test_singleton_class_return_val(self, space):
        w_res = space.execute("""
        class X
        end

        x = X.new
        return (class << x
          5
        end)
        """)
        assert space.int_w(w_res) == 5

    def test_constant(self, space):
        w_res = space.execute("Abc = 3; return Abc")
        assert space.int_w(w_res)

        assert space.w_object.constants_w["Abc"] is w_res

    def test_class_constant(self, space):
        w_res = space.execute("""
        class X
          Constant = 3
          def f
            return Constant
          end
        end
        return X.new.f
        """)
        assert space.int_w(w_res) == 3
        assert "Constant" not in space.w_object.constants_w

    def test_module_constant(self, space):
        w_res = space.execute("""
        ExternalConst = 10
        module Y
          Constant = 5
          OtherConstant = ExternalConst
        end
        return [Y::Constant, Y::OtherConstant]
        """)
        assert self.unwrap(space, w_res) == [5, 10]

    def test_subclass_constant(self, space):
        w_res = space.execute("""
        GlobalConstant = 5
        class X
          Constant = 3
        end
        class Y < X
          def f
            [Constant, GlobalConstant]
          end
        end
        return Y.new.f
        """)
        assert self.unwrap(space, w_res) == [3, 5]

    def test_subclass_non_class(self, space):
        with self.raises(space, "TypeError", "wrong argument type String (expected Class)"):
            space.execute("""
            class Y < "abc"
            end
            """)

    def test_class_constant_block(self, space):
        w_res = space.execute("""
        class X
          Constant = 5
          def f
            (1..3).map do
              Constant
            end
          end
        end
        return X.new.f
        """)
        assert self.unwrap(space, w_res) == [5, 5, 5]

    def test_nonmodule_constant(self, space):
        with self.raises(space, "TypeError", "3 is not a class/module"):
            space.execute("3::Foo")

    def test_instance_var(self, space):
        w_res = space.execute("""
        class X
          def set val
            @a = val
          end
          def get
            @a
          end
        end
        x = X.new
        x.set 3
        x.set "abc"
        return x.get
        """)
        assert space.str_w(w_res) == "abc"

    def test_send_block(self, space):
        w_res = space.execute("""
        res = []
        [1, 2, 3].each do |x|
          res << (x * 2)
        end
        return res
        """)
        assert self.unwrap(space, w_res) == [2, 4, 6]

    def test_send_block_with_block_arg(self, space):
        w_res = space.execute("""
        res = []
        block = proc do |&b|
          [1, 2, 3].each do |x|
            res << b.call(x)
          end
        end
        block.call { |x| 2 * x }
        return res
        """)
        assert self.unwrap(space, w_res) == [2, 4, 6]

    def test_send_block_with_opt_args(self, space):
        w_res = space.execute("""
        res = []
        block = proc { |b='b'| res << b }
        block.call('a')
        block.call
        return res
        """)
        assert self.unwrap(space, w_res) == ['a', 'b']
        w_res = space.execute("""
        res = []
        [1, 2, 3].each do |x, y="y"|
          res << x << y
        end
        return res
        """)
        assert self.unwrap(space, w_res) == [1, 'y', 2, 'y', 3, 'y']
        w_res = space.execute("""
        res = []
        block = proc do |x, y="y", *rest, &block|
          res << x << y << rest
          block.call(res)
        end
        block.call(1) { |res| res << "block called" }
        return res
        """)
        assert self.unwrap(space, w_res) == [1, 'y', [], "block called"]

    def test_yield(self, space):
        w_res = space.execute("""
        class X
          def f
            yield 2, 3
            yield 4, 5
          end
        end

        res = []
        X.new.f do |x, y|
          res << (x - y)
        end
        return res
        """)
        assert self.unwrap(space, w_res) == [-1, -1]

    def test_range(self, space):
        w_res = space.execute("return (1..10).begin")
        assert space.int_w(w_res) == 1
        w_res = space.execute("return (1..10).end")
        assert space.int_w(w_res) == 10
        w_res = space.execute("return (1...10).end")
        assert space.int_w(w_res) == 10

    def test_augmented_assignment(self, space):
        w_res = space.execute("i = 0; i += 5; return i")
        assert space.int_w(w_res) == 5
        w_res = space.execute("""
        class X
          attr_accessor :a
          def initialize
            self.a = 5
          end
        end
        x = X.new
        x.a += 5
        return x.a
        """)
        assert space.int_w(w_res) == 10

        w_res = space.execute("""
        class Counter
          attr_reader :value
          def initialize start
            @value = start
          end
          def incr
            @value += 1
          end
        end

        c = Counter.new 0
        c.incr
        c.incr
        c.incr
        return c.value
        """)
        assert space.int_w(w_res) == 3

    def test_or_equal(self, space):
        w_res = space.execute("""
        x = nil
        x ||= 5
        v = x
        x ||= 3
        return [v, x]
        """)
        assert self.unwrap(space, w_res) == [5, 5]
        w_res = space.execute("""
        x = [nil]
        x[0] ||= 5
        return x
        """)
        assert self.unwrap(space, w_res) == [5]

    def test_lookup_constant(self, space):
        w_res = space.execute("""
        class X
          Constant = 3
        end
        return X::Constant
        """)
        assert space.int_w(w_res) == 3
        w_res = space.execute("""
        class X
          Constant = 3
          def self.constant
            Constant
          end
        end
        return X.constant
        """)
        assert space.int_w(w_res) == 3
        w_res = space.execute("""
        X = 3
        return ::X
        """)
        assert space.int_w(w_res) == 3

    def test___FILE__(self, space):
        w_res = space.execute("return __FILE__")
        assert space.str_w(w_res) == "-e"

    def test___LINE__(self, space):
        w_res = space.execute("""
        return \\
           [__LINE__,
           __LINE__]
        """)
        assert self.unwrap(space, w_res) == [3, 4]

    def test_default_arguments(self, space):
        w_res = space.execute("""
        def f(a, b=3, c=b)
          [a, b, c]
        end
        return f 1
        """)
        assert self.unwrap(space, w_res) == [1, 3, 3]
        w_res = space.execute("return f 5, 6")
        assert self.unwrap(space, w_res) == [5, 6, 6]
        w_res = space.execute("return f 5, 6, 10")
        assert self.unwrap(space, w_res) == [5, 6, 10]

    def test_module(self, space):
        w_res = space.execute("""
        module M
          def oninstanceonly
            5
          end
        end
        return M
        """)
        assert isinstance(w_res, W_ModuleObject)
        assert w_res.name == "M"

        with self.raises(space, "NoMethodError"):
            space.execute("M.oninstanceonly")

    def test_module_reopen_non_module(self, space):
        space.execute("""
        module Foo
          Const = nil
          class X
          end
        end
        """)
        with self.raises(space, "TypeError", "Const is not a module"):
            space.execute("""
            module Foo::Const
            end
            """)
        with self.raises(space, "TypeError", "X is not a module"):
            space.execute("""
            module Foo::X
            end
            """)

    def test_module_reopen_scope(self, space):
        w_res = space.execute("""
        class Foo
        end

        module Bar
          module Foo
          end
        end
        return Foo, Bar::Foo
        """)
        [w_cls1, w_cls2] = space.listview(w_res)
        assert w_cls1 is not w_cls2

    def test_singleton_method(self, space):
        w_res = space.execute("""
        def Array.hello
          "hello world"
        end

        return Array.hello
        """)
        assert space.str_w(w_res) == "hello world"

        with self.raises(space, "NoMethodError"):
            space.execute("[].hello")

    def test_splat(self, space):
        w_res = space.execute("""
        def f(a, b, c, d, e, f)
          [a, b, c, d, e, f]
        end

        return f(*2, *[5, 3], *[], 7, 8, *[1], *nil)
        """)
        assert self.unwrap(space, w_res) == [2, 5, 3, 7, 8, 1]

        w_res = space.execute("""
        class ToA
          def to_a
            [1, 2, 3, 4, 5, 6]
          end
        end

        return f *ToA.new
        """)
        assert self.unwrap(space, w_res) == [1, 2, 3, 4, 5, 6]

        w_res = space.execute("""
        class ToAry
          def to_ary
            [1, 5, 6, 7, 8, 9]
          end
        end

        return f *ToAry.new
        """)
        assert self.unwrap(space, w_res) == [1, 5, 6, 7, 8, 9]

    def test_send_block_splat(self, space):
        w_res = space.execute("""
        def f(a)
          x = yield
          return a + x
        end

        return f(*2) { 5 }
        """)
        assert space.int_w(w_res) == 7
        w_res = space.execute("""
        def f(&a)
          return a
        end
        return f(*[], &nil)
        """)
        assert w_res is space.w_nil

    def test_global_variables(self, space):
        w_res = space.execute("return $abc")
        assert w_res is space.w_nil
        w_res = space.execute("$abc = 3; return $abc")
        assert space.int_w(w_res) == 3

    def test_assign_constant(self, space):
        w_res = space.execute("""
        class X
        end
        X::Constant = 5
        return X::Constant
        """)
        assert space.int_w(w_res) == 5
        with self.raises(space, "NameError"):
            space.execute("Constant")

    def test_receive_splat_argument(self, space):
        w_res = space.execute("""
        def f(*args)
          args
        end

        return f(1, 2, *[3, 4])
        """)
        assert self.unwrap(space, w_res) == [1, 2, 3, 4]

        w_res = space.execute("""
        def f(*args)
          'hi'
        end

        return f(1, 2, *[3, 4])
        """)
        assert self.unwrap(space, w_res) == 'hi'

        w_res = space.execute("""
        def f(h, *)
          h
        end

        return f(1, 2, *[3, 4])
        """)
        assert self.unwrap(space, w_res) == 1

    def test_or(self, space):
        w_res = space.execute("return 3 + 4 || 5")
        assert space.int_w(w_res) == 7
        w_res = space.execute("return nil || 12")
        assert space.int_w(w_res) == 12

    def test_not(self, space):
        w_res = space.execute("return !3")
        assert w_res is space.w_false
        w_res = space.execute("return !!3")
        assert w_res is space.w_true

    def test_subscript_assignment(self, space):
        w_res = space.execute("""
        x = [0]
        x[0] = 5
        return x[0]
        """)
        assert space.int_w(w_res) == 5
        w_res = space.execute("""
        x = [0]
        x[0] += 2
        return x[0]
        """)
        assert space.int_w(w_res) == 2
        w_res = space.execute("""
        x = [0]
        x[*[0]] = 45
        return x[0]
        """)
        assert space.int_w(w_res) == 45

    def test_empty_hash(self, space):
        space.execute("return {}")

    def test_multiple_assignment(self, space):
        w_res = space.execute("""
        a = [3]
        a[0], Object::Const, b = [5, 4]
        return [a, Object::Const, b]
        """)
        assert self.unwrap(space, w_res) == [[5], 4, None]

    def test_splat_assignment(self, space):
        w_res = space.execute("""
        class X
          def to_a
            return nil
          end
        end
        x = X.new
        a = *x
        return a == [x]
        """)
        assert w_res is space.w_true
        w_res = space.execute("""
        *a = nil
        return a
        """)
        assert self.unwrap(space, w_res) == [None]

    def test_splat_lhs_assignment(self, space):
        w_res = space.execute("""
        a, *b, c = *[1,2]
        return [a, b, c]
        """)
        assert self.unwrap(space, w_res) == [1, [], 2]
        w_res = space.execute("""
        a, *b, c = 1,2,3,4
        return [a, b, c]
        """)
        assert self.unwrap(space, w_res) == [1, [2, 3], 4]
        w_res = space.execute("""
        a, *b, c = 1
        return [a, b, c]
        """)
        assert self.unwrap(space, w_res) == [1, [], None]
        w_res = space.execute("""
        a, = 3, 4
        return a
        """)
        assert space.int_w(w_res) == 3

    def test_destructuring_assignment(self, space):
        w_res = space.execute("""
        (a, b, (c, d, *e)) = [1, 2, [3, 4]]
        return a, b, c, d, e
        """)
        assert self.unwrap(space, w_res) == [1, 2, 3, 4, []]
        w_res = space.execute("""
        a, *b, (c, (d, *, e), ) = 1, 2, 3, [4, [5, "ignored", "ignored", 6], 7]
        return a, b, c, d, e
        """)
        assert self.unwrap(space, w_res) == [1, [2, 3], 4, 5, 6]

    def test_minus(self, space):
        w_res = space.execute("""
        def a(x)
          Math.sin(x)
        end
        b = 1
        c = 1
        return [(a -b), (c -b)]
        """)
        assert self.unwrap(space, w_res) == [math.sin(-1), 0]

    def test_case(self, space):
        w_res = space.execute("""
        res = []
        4.times do |i|
          case i
          when 0, 1
            res << 0
          when 2
            res << 1
          else
            res << 2
          end
        end
        return res
        """)
        assert self.unwrap(space, w_res) == [0, 0, 1, 2]

    def test_dynamic_string(self, space):
        w_res = space.execute("""
        x = 123
        return "abc, #{x}, easy"
        """)
        assert space.str_w(w_res) == "abc, 123, easy"

    def test_dynamic_regexp(self, space):
        w_res = space.execute("""
        x = 123
        return /#{x}/.source
        """)
        assert space.str_w(w_res) == "123"

    def test_regexp_sytnax_error(self, space):
        with self.raises(space, "SyntaxError"):
            space.execute("/(/")

    def test_class_variable_from_module_accessed_from_instance_side(self, space):
        w_res = space.execute("""
        module A
          @@foo = 'a'
        end

        class B
          include A

          def get
            @@foo
          end
        end

        return B.new.get
        """)
        assert space.str_w(w_res) == 'a'

    def test_class_variable_accessed_from_instance_side(self, space):
        w_res = space.execute("""
        class A; end
        class B < A
          @@foo = "B"
          def get; @@foo; end
        end
        in_subclass = [B.new.get]
        class A; @@foo = "A overrides all"; end
        return in_subclass + [B.new.get]
        """)
        assert self.unwrap(space, w_res) == ["B", "A overrides all"]

    def test_class_variables_accessed_from_class_side(self, space):
        w_res = space.execute("""
        class A; @@foo = 'A'; end
        class B < A
          def get; @@foo; end
          def self.get; @@foo; end
        end
        return [B.get, B.new.get]
        """)
        assert self.unwrap(space, w_res) == ['A', 'A']

    def test_class_variable_access_has_static_scope(self, space):
        with self.raises(space, "NameError"):
            space.execute("""
            class A
              def get
                @@foo
              end
            end
            class B < A;
              @@foo = "b"
            end
            B.new.get
            """)

    def test_ancestors(self, space):
        w_res = space.execute("""
        class A
        end

        class B < A
        end

        module C
        end

        module D
          include C
        end

        ary = [A.ancestors, B.ancestors, C.ancestors, D.ancestors]

        B.include D
        ary << B.ancestors
        return ary
        """)
        a = self.find_const(space, 'A')
        b = self.find_const(space, 'B')
        c = self.find_const(space, 'C')
        d = self.find_const(space, 'D')
        assert self.unwrap(space, w_res) == [
            [a, space.w_object, space.w_kernel, space.w_basicobject],
            [b, a, space.w_object, space.w_kernel, space.w_basicobject],
            [c],
            [d, c],
            [b, d, c, a, space.w_object, space.w_kernel, space.w_basicobject]
        ]

    def test_lookup_for_includes(self, space):
        w_res = space.execute("""
        class A
          def self.get; "A.get"; end
          def get; "A#get"; end
          def override; "A#override"; end
        end
        module M
          def get; "M#get"; end
          def override; "M#override"; end
        end
        class B < A
          def override; "B#override"; end
          include M
        end
        res = [B.get, B.new.get, B.new.override]
        module M
          def get; "M#get (2nd ed)"; end
        end
        return res << B.new.get
        """)
        assert self.unwrap(space, w_res) == ["A.get", "M#get", "B#override", "M#get (2nd ed)"]

    def test_find_const(self, space):
        with self.raises(space, "NameError"):
            space.execute("""
            class A
              Const = "A"
              class InnerA; end
            end

            class B < A::InnerA
              # Const lookup in superclass does not
              # traverse lexical scope of superclass,
              # and A::InnerA syntax doesn't put B in
              # the lexical scope of A
              Const
            end
            """)

        w_res = space.execute("""
        class A
          Const = "A"
          class InnerA
            InnerConst = Const
          end
        end

        class B < A::InnerA
          BConst = InnerConst
        end
        return B::BConst
        """)
        assert self.unwrap(space, w_res) == "A"

    def test_module_find_const(self, space):
        w_res = space.execute("""
        module M
          ABC = 1
        end
        Object.send :include, M
        module Y
          ABC
        end
        return Y::ABC
        """)
        assert self.unwrap(space, w_res) == 1

    def test_defined(self, space):
        w_res = space.execute("return [defined? A, defined? Array]")
        assert self.unwrap(space, w_res) == [None, "constant"]
        w_res = space.execute("""
        @a = 3
        return [defined? @a, defined? @b]
        """)
        assert self.unwrap(space, w_res) == ["instance-variable", None]
        w_res = space.execute("""
        return [defined? self, defined? nil, defined? true, defined? false]
        """)
        assert self.unwrap(space, w_res) == ["self", "nil", "true", "false"]
        w_res = space.execute("""
        return [defined? nil.nil?, defined? nil.fdfdafa]
        """)
        assert self.unwrap(space, w_res) == ["method", None]
        w_res = space.execute("""
        return [defined? a = 3]
        """)
        assert self.unwrap(space, w_res) == ["assignment"]
        w_res = space.execute("""
        a = 3
        return defined?(a)
        """)
        assert space.str_w(w_res) == "local-variable"
        w_res = space.execute("""
        a = 3
        return defined?((1; a))
        """)
        assert space.str_w(w_res) == "local-variable"
        w_res = space.execute("""
        return defined?((a, b = 3))
        """)
        assert space.str_w(w_res) == "assignment"
        w_res = space.execute("""
        return defined?((a += 2))
        """)
        assert space.str_w(w_res) == "assignment"
        w_res = space.execute("""
        return [defined?((a ||= 2)), defined?((a &&= 3))]
        """)
        assert self.unwrap(space, w_res) == ["assignment", "assignment"]
        w_res = space.execute("""
        return [defined?(3 and false), defined?(false or true)]
        """)
        assert self.unwrap(space, w_res) == ["expression", "expression"]
        w_res = space.execute("""
        return [defined?('abc'), defined?("abc#{42}")]
        """)
        assert self.unwrap(space, w_res) == ["expression", "expression"]
        w_res = space.execute("""
        return [defined?(/abc/), defined?(/abc#{42}/)]
        """)
        assert self.unwrap(space, w_res) == ["expression", "expression"]
        w_res = space.execute("""
        return defined?(1..2)
        """)
        assert space.str_w(w_res) == "expression"
        w_res = space.execute("""
        return defined?([1, 2, 3])
        """)
        assert space.str_w(w_res) == "expression"
        w_res = space.execute("""
        return defined?({1 => 2})
        """)
        assert space.str_w(w_res) == "expression"
        w_res = space.execute("""
        $abc = 3
        return [defined?($abc), defined?($abd)]
        """)
        assert self.unwrap(space, w_res) == ["global-variable", None]
        w_res = space.execute("""
        class A
          @@abc = 3
          def m
            return [defined?(@@abc), defined?(@@abd)]
          end
        end
        return A.new.m
        """)
        assert self.unwrap(space, w_res) == ["class variable", None]
        w_res = space.execute("""
        def f
          defined?(yield)
        end

        return [f, f(&:a)]
        """)
        assert self.unwrap(space, w_res) == [None, "yield"]
        w_res = space.execute("""
        class B
          def a
          end
        end
        class C < B
          def a
            defined?(super)
          end
          def b
            defined?(super())
          end
        end
        return [C.new.a, C.new.b]
        """)
        assert self.unwrap(space, w_res) == ["super", None]

    def test_defined_unscoped_constant(self, space):
        w_res = space.execute("return defined? ::Foobar")
        assert w_res is space.w_nil
        w_res = space.execute("return defined? ::Fixnum")
        assert self.unwrap(space, w_res) == "constant"

    def test_match(self, space):
        w_res = space.execute("return 3 =~ nil")
        assert self.unwrap(space, w_res) is None

    def test_not_match(self, space):
        w_res = space.execute("return 3 !~ nil")
        assert self.unwrap(space, w_res)

    def test_super(self, space):
        w_res = space.execute("""
        class A
          def f(a, b)
            return [a, b]
          end
        end
        class B < A
          def f(a, b)
            a += 10
            return super
          end
        end
        return B.new.f(4, 5)
        """)
        assert self.unwrap(space, w_res) == [14, 5]

        w_res = space.execute("""
        class C < A
          def f
            super(*[1, 2])
          end
        end
        return C.new.f
        """)
        assert self.unwrap(space, w_res) == [1, 2]

    def test_super_block(self, space):
        w_res = space.execute("""
        class A
          def f a
            a + yield
          end
        end

        class B < A
          def f
            super(2) { 5 }
          end
        end

        return B.new.f
        """)
        assert space.int_w(w_res) == 7
        w_res = space.execute("""
        class C < A
          def f
            super(*[2]) { 12 }
          end
        end

        return C.new.f
        """)
        assert space.int_w(w_res) == 14
        w_res = space.execute("""
        class D < A
          def f a
            super
          end
        end

        return D.new.f(3) { 12 }
        """)
        assert space.int_w(w_res) == 15

    def test_next_loop(self, space):
        w_res = space.execute("""
        res = []
        i = 0
        while i < 10
          i += 1
          if i > 3
            next
          end
          res << i
        end
        return res
        """)
        assert self.unwrap(space, w_res) == [1, 2, 3]

    def test_next_loop_block(self, space):
        w_res = space.execute("""
        a = []
        2.times {
          i = 0
          while i < 3
            i += 1
            a << i
            next
            raise "abc"
          end
        }
        return a
        """)
        assert self.unwrap(space, w_res) == [1, 2, 3, 1, 2, 3]

    def test_break_loop(self, space):
        w_res = space.execute("""
        res = []
        i = 0
        other = while i < 10
          i += 1
          if i > 3
              break 200
          end
          res << i
        end
        res << other
        return res
        """)
        assert self.unwrap(space, w_res) == [1, 2, 3, 200]

    def test_simple_lexical_scope_constant(self, space):
        w_res = space.execute("""
        class A
          CONST = 1

          def get
            CONST
          end
        end

        class B < A
          CONST = 2
        end

        return A.new.get == B.new.get
        """)
        assert space.is_true(w_res)

    def test_complex_lexical_scope_constant(self, space):
        space.execute("""
        class Bar
          module M
          end
        end

        module X
          module M
            FOO = 5
          end

          class Foo < Bar
            def f
              M::FOO
            end
          end
        end

        class X::Foo
          def g
            M::FOO
          end
        end
        """)
        w_res = space.execute("return X::Foo.new.f")
        assert space.int_w(w_res) == 5
        with self.raises(space, "NameError"):
            space.execute("X::Foo.new.g")

    def test_lexical_scope_singletonclass(self, space):
        space.execute("""
        class M
          module NestedModule
          end

          class << self
            include NestedModule
          end
        end
        """)

    def test_constant_lookup_from_trpl_book(self, space):
        w_res = space.execute("""
        module Kernel
          A = B = C = D = E = F = "defined in kernel"
        end
        A = B = C = D = E = "defined at toplevel"

        class Super
          A = B = C = D = "defined in superclass"
        end

        module Included
          A = B = C = "defined in included module"
        end

        module Enclosing
          A = B = "defined in enclosing module"

          class Local < Super
            include Included
            A = "defined Locally"
            RESULT = [A, B, C, D, E, F]
          end
        end
        return Enclosing::Local::RESULT
        """)
        assert self.unwrap(space, w_res) == [
            "defined Locally",
            "defined in enclosing module",
            "defined in included module",
            "defined in superclass",
            "defined at toplevel",
            "defined in kernel"
        ]

    def test_top_level_include(self, space):
        w_res = space.execute("""
        module M
          Foo = 10
        end
        include M
        return Foo
        """)
        assert space.int_w(w_res) == 10

    def test_call_too_few_args(self, space):
        space.execute("""
        def f(a, b=2)
        end
        def g(a, b, *c)
        end
        """)
        with self.raises(space, "ArgumentError", "wrong number of arguments (0 for 1)"):
            space.execute("f")
        with self.raises(space, "ArgumentError", "wrong number of arguments (0 for 2)"):
            space.execute("g")

    def test_call_too_many_args(self, space):
        space.execute("""
        def f
        end
        """)
        with self.raises(space, "ArgumentError", "wrong number of arguments (3 for 0)"):
            space.execute("f 1, 2, 3")

    def test_call_too_few_args_builtin(self, space):
        with self.raises(space, "ArgumentError", "wrong number of arguments (0 for 1)"):
            space.execute("1.send(:+)")

    def test_call_too_many_args_builtin(self, space):
        with self.raises(space, "ArgumentError", "wrong number of arguments (3 for 1)"):
            space.execute("1.send(:+, 2, 3, 4)")

    def test_bignum(self, space):
        w_res = space.execute("return 18446744073709551628.to_s")
        assert space.str_w(w_res) == "18446744073709551628"
        w_res = space.execute("return 18446744073709551628.class")
        assert w_res is space.w_bignum

    def test_lambda(self, space):
        w_res = space.execute("return ->{ 1 + 1 }.call")
        assert space.int_w(w_res) == 2


class TestBlocks(BaseTopazTest):
    def test_self(self, space):
        w_res = space.execute("""
        class X
          def initialize
            @data = []
          end
          def process d
            d.each do |x|
              @data << x * 2
            end
          end
          def data
            @data
          end
        end

        x = X.new
        x.process [1, 2, 3]
        return x.data
        """)
        assert self.unwrap(space, w_res) == [2, 4, 6]

    def test_param_is_cell(self, space):
        w_res = space.execute("""
        def sum(arr, start)
          arr.each do |x|
            start += x
          end
          start
        end

        return sum([1, 2, 3], 4)
        """)
        assert space.int_w(w_res) == 10

    def test_nested_block(self, space):
        w_res = space.execute("""
        result = []
        [1, 2, 3].each do |x|
          [3, 4, 5].each do |y|
            result << x - y
          end
        end
        return result
        """)
        assert self.unwrap(space, w_res) == [-2, -3, -4, -1, -2, -3, 0, -1, -2]

    def test_no_accepted_arguments(self, space):
        w_res = space.execute("""
        result = []
        2.times do
          result << "hello"
        end
        return result
        """)
        assert self.unwrap(space, w_res) == ["hello", "hello"]

    def test_multi_arg_block_array(self, space):
        w_res = space.execute("""
        res = []
        [[1, 2], [3, 4]].each do |x, y|
          res << x - y
        end
        return res
        """)
        assert self.unwrap(space, w_res) == [-1, -1]

    def test_block_argument(self, space):
        w_res = space.execute("""
        def f(&b)
          b.call
        end
        return f { 5 }
        """)
        assert space.int_w(w_res) == 5

        w_res = space.execute("""
        def g(&b)
          b
        end
        return g
        """)
        assert w_res is space.w_nil

        w_res = space.execute("""
        def h(&b)
          [1, 2, 3].map { |x| b.call(x) }
        end
        return h { |x| x * 3 }
        """)
        assert self.unwrap(space, w_res) == [3, 6, 9]

    def test_block_argument_send(self, space):
        w_res = space.execute("""
        f = lambda { |x| x * 2 }
        return [1, 2, 3].map(&f)
        """)
        assert self.unwrap(space, w_res) == [2, 4, 6]
        w_res = space.execute("""
        def x(&b)
          b
        end
        return x(&nil)
        """)
        assert w_res is space.w_nil

        with self.raises(space, "TypeError", "wrong argument type"):
            space.execute("f(&3)")

        w_res = space.execute("""
        return [1, 2, 3].map(&:to_s)
        """)
        assert self.unwrap(space, w_res) == ["1", "2", "3"]

        with self.raises(space, "TypeError", "can't convert String to Proc (String#to_proc gives String)"):
            space.execute("""
            class String; def to_proc; self; end; end
            [1, 2, 3].map(&"to_s")
            """)

    def test_too_few_block_arguments(self, space):
        w_res = space.execute("""
        def f
          yield 1
        end
        return f { |a,b,c| [a,b,c] }
        """)
        assert self.unwrap(space, w_res) == [1, None, None]

    def test_block_return(self, space):
        w_res = space.execute("""
        def f
          yield
          10
        end
        def g
          f { return 15 }
          5
        end
        return g
        """)
        assert space.int_w(w_res) == 15

    def test_nested_block_return(self, space):
        w_res = space.execute("""
        def f
          [1].each do |x|
            [x].each do |y|
              return y
            end
          end
          3
        end
        return f
        """)
        assert space.int_w(w_res) == 1

    def test_nested_block_dead_frame_return(self, space):
        w_res = space.execute("""
        class SavedInnerBlock
          attr_accessor :record

          def outer
            yield
            @block.call
          end

          def inner
            yield
          end

          def start
            outer do
              inner do
                @block = proc do
                  self.record = :before_return
                  return :return_value
                end
              end
            end
            self.record = :bottom_of_start
            return false
          end
        end

        sib = SavedInnerBlock.new
        return [sib.start, sib.record]
        """)
        assert self.unwrap(space, w_res) == ["return_value", "before_return"]

    def test_break_block(self, space):
        w_res = space.execute("""
        def f(res, &a)
          begin
            g(&a)
          ensure
            res << 1
          end
          5
        end

        def g()
          4 + yield
        end

        res = []
        res << (f(res) { break 3})
        return res
        """)
        assert self.unwrap(space, w_res) == [1, 3]

    def test_break_nested_block(self, space):
        w_res = space.execute("""
        def f
          yield
        end

        return f {
          a = []
          3.times do |i|
            begin
              a << :begin
              next if i == 0
              break if i == 2
              a << :begin_end
            ensure
              a << :ensure
            end
            a << :after
          end
          a
        }
        """)
        assert self.unwrap(space, w_res) == ["begin", "ensure", "begin", "begin_end", "ensure", "after", "begin", "ensure"]

    def test_break_block_frame_exited(self, space):
        space.execute("""
        def create_block
          b = capture_block do
            break
          end
        end

        def capture_block(&b)
          b
        end
        """)
        with self.raises(space, "LocalJumpError", "break from proc-closure"):
            space.execute("create_block.call")

    def test_singleton_class_block(self, space):
        w_res = space.execute("""
        def f(o)
          class << o
            yield
          end
        end

        return f(Object.new) { 123 }
        """)
        assert space.int_w(w_res) == 123

    def test_yield_no_block(self, space):
        space.execute("""
        def f
          yield
        end
        """)
        with self.raises(space, "LocalJumpError"):
            space.execute("f")

    def test_splat_arg_block(self, space):
        w_res = space.execute("""
        def f a, b, c
          yield a, b, c
        end

        return f(2, 3, 4) { |*args| args }
        """)
        assert self.unwrap(space, w_res) == [2, 3, 4]

    def test_yield_splat(self, space):
        w_res = space.execute("""
        def f(*args)
          yield *args
        end

        return f(3, 5) { |a, b| a + b }
        """)
        assert space.int_w(w_res) == 8
        w_res = space.execute("""
        def f
          yield 3, *[4, 5]
        end
        return f() { |a, b, c| a * b + c}
        """)
        assert space.int_w(w_res) == 17

    def test_destructuring_arg_block(self, space):
        w_res = space.execute("""
        res = []
        hash = {1 => [2, [3, "ignored", 4]]}
        ky, a, b, c, d = nil, nil, nil, nil, nil
        hash.each_pair do |ky, (a, (b, *c, d))|
          res << ky << a << b << c << d
        end
        res << ky << a << b << c << d
        return res
        """)
        assert self.unwrap(space, w_res) == [
            1, 2, 3, ["ignored"], 4,
            None, None, None, None, None
        ]

    def test_block_local_var(self, space):
        w_res = space.execute("""
        def f
            yield
        end

        x = 3
        f { |;x| x = 5 }
        return x
        """)
        assert space.int_w(w_res) == 3


class TestExceptions(BaseTopazTest):
    def test_simple(self, space):
        w_res = space.execute("""
        return begin
          1 / 0
        rescue ZeroDivisionError
          5
        end
        """)
        assert space.int_w(w_res) == 5

    def test_bind_to_name(self, space):
        w_res = space.execute("""
        return begin
          1 / 0
        rescue ZeroDivisionError => e
          e.to_s
        end
        """)
        assert space.str_w(w_res) == "divided by 0"

    def test_rescue_no_exception(self, space):
        w_res = space.execute("""
        return begin
          1 + 1
        rescue ZeroDivisionError
          5
        end
        """)
        assert space.int_w(w_res) == 2

    def test_uncaught_exception(self, space):
        with self.raises(space, "NoMethodError"):
            space.execute("""
            begin
              [].dsafdsafsa
            rescue ZeroDivisionError
              5
            end
            """)

    def test_multiple_rescues(self, space):
        w_res = space.execute("""
        return begin
          1 / 0
        rescue NoMethodError
          5
        rescue ZeroDivisionError
          10
        end
        """)
        assert space.int_w(w_res) == 10

    def test_nested_rescue(self, space):
        w_res = space.execute("""
        return begin
          begin
            1 / 0
          rescue NoMethodError
            10
          end
        rescue ZeroDivisionError
          5
        end
        """)
        assert space.int_w(w_res) == 5

    def test_simple_ensure(self, space):
        w_res = space.execute("""
        res = []
        begin
          res << 1
          1 / 0
        rescue ZeroDivisionError
          res << 2
        ensure
          res << 3
        end
        return res
        """)
        assert self.unwrap(space, w_res) == [1, 2, 3]

    def test_ensure_return(self, space):
        w_res = space.execute("""
        res = []
        begin
          return res
        ensure
          res << 1
        end
        """)
        assert self.unwrap(space, w_res) == [1]

    def test_ensure_block_return(self, space):
        w_res = space.execute("""
        def h
          yield
        end
        def g(res)
          h {
            begin
              return 5
            ensure
              res << 12
            end
          }
          10
        end
        def f
          res = []
          res << g(res)
          res
        end
        return f
        """)
        assert self.unwrap(space, w_res) == [12, 5]

    def test_ensure_nonlocal_block_return(self, space):
        w_res = space.execute("""
        def h
          yield
        end
        def g(res, &a)
          begin
            yield
          ensure
            res << 1
          end
        end
        def f(res)
          g(res) { return 5 }
        end
        res = []
        res << f(res)
        return res
        """)
        assert self.unwrap(space, w_res) == [1, 5]

    def test_ensure_result(self, space):
        w_res = space.execute("""
        return begin
        ensure
          nil
        end
        """)
        assert w_res is space.w_nil

    def test_rescue_loop(self, space):
        w_res = space.execute("""
        i = 0
        while i < 3
          begin
            [].asdef
          rescue NoMethodError
            i += 1
          end
        end
        return i
        """)
        assert space.int_w(w_res) == 3

    def test_rescue_superclass(self, space):
        w_res = space.execute("""
        begin
          1 / 0
        rescue StandardError
          return 0
        end
        """)
        assert space.int_w(w_res) == 0

    def test_bang_method_call_without_parens(self, space):
        w_res = space.execute("""
        ! respond_to? :asdf
        """)
        assert w_res is space.w_true
