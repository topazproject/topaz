import math

from rupypy.objects.boolobject import W_TrueObject
from rupypy.objects.moduleobject import W_ModuleObject
from rupypy.objects.objectobject import W_Object

from .base import BaseRuPyPyTest


class TestInterpreter(BaseRuPyPyTest):
    def test_add(self, ec):
        w_res = ec.space.execute(ec, "1 + 1")
        assert isinstance(w_res, W_TrueObject)

    def test_global_send(self, ec, capfd):
        ec.space.execute(ec, "puts 1")
        out, err = capfd.readouterr()
        assert out == "1\n"
        assert not err

    def test_obj_send(self, ec):
        w_res = ec.space.execute(ec, "return 1.to_s")
        assert ec.space.str_w(w_res) == "1"

    def test_variables(self, ec):
        w_res = ec.space.execute(ec, "a = 100; return a")
        assert ec.space.int_w(w_res) == 100

    def test_if(self, ec):
        w_res = ec.space.execute(ec, "if 3 then return 2 end")
        assert ec.space.int_w(w_res) == 2

        w_res = ec.space.execute(ec, "x = if 3 then 5 end; return x")
        assert ec.space.int_w(w_res) == 5

        w_res = ec.space.execute(ec, "x = if false then 5 end; return x")
        assert w_res is ec.space.w_nil

        w_res = ec.space.execute(ec, "x = if nil then 5 end; return x")
        assert w_res is ec.space.w_nil

        w_res = ec.space.execute(ec, "x = if 3 then end; return x")
        assert w_res is ec.space.w_nil

    def test_while(self, ec):
        w_res = ec.space.execute(ec, """
        i = 0
        while i < 1
            i += 1
        end
        return i
        """)
        assert ec.space.int_w(w_res) == 1

        w_res = ec.space.execute(ec, """
        x = while false do end
        return x
        """)
        assert w_res is ec.space.w_nil

    def test_return(self, ec):
        w_res = ec.space.execute(ec, "return 4")
        assert ec.space.int_w(w_res) == 4

    def test_array(self, ec):
        w_res = ec.space.execute(ec, "return [[1], [2], [3]]")
        assert [[ec.space.int_w(w_y) for w_y in ec.space.listview(w_x)] for w_x in ec.space.listview(w_res)] == [[1], [2], [3]]

    def test_def_function(self, ec):
        w_res = ec.space.execute(ec, "return def f() end")
        assert w_res is ec.space.w_nil

        w_res = ec.space.execute(ec, """
        def f(a, b)
            a + b
        end
        return f 1, 2
        """)
        assert ec.space.int_w(w_res) == 3
        w_res = ec.space.execute(ec, "return Object.f(5, -2)")
        assert ec.space.int_w(w_res) == 3

    def test_interpreter(self, ec):
        w_res = ec.space.execute(ec, 'return "abc"')
        assert ec.space.str_w(w_res) == "abc"

        w_res = ec.space.execute(ec, """
        def test
            x = ""
            x << "abc"
        end

        return [test, test]
        """)

        assert [ec.space.str_w(w_s) for w_s in ec.space.listview(w_res)] == ["abc", "abc"]

    def test_class(self, ec):
        w_res = ec.space.execute(ec, """
        class X
            def m
                self
            end

            def f
                2
            end
        end
        """)
        w_cls = ec.space.getclassfor(W_Object).constants_w["X"]
        assert w_cls.methods_w.viewkeys() == {"m", "f"}

        w_res = ec.space.execute(ec, """
        class Z < X
            def g
                3
            end
        end

        z = Z.new
        return [z.f, z.g]
        """)
        assert [ec.space.int_w(w_x) for w_x in ec.space.listview(w_res)] == [2, 3]

    def test_reopen_class(self, ec):
        ec.space.execute(ec, """
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
        w_cls = ec.space.getclassfor(W_Object).constants_w["X"]
        assert w_cls.methods_w.viewkeys() == {"m", "f"}

    def test_singleton_class(self, ec):
        w_res = ec.space.execute(ec, """
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
        assert ec.space.int_w(w_res) == 6

        with self.raises("NoMethodError"):
            ec.space.execute(ec, "X.new.m")

    def test_constant(self, ec):
        w_res = ec.space.execute(ec, "Abc = 3; return Abc")
        assert ec.space.int_w(w_res)

        w_object_cls = ec.space.getclassfor(W_Object)
        assert w_object_cls.constants_w["Abc"] is w_res

    def test_class_constant(self, ec):
        w_res = ec.space.execute(ec, """
        class X
            Constant = 3
            def f
                return Constant
            end
        end
        return X.new.f
        """)
        assert ec.space.int_w(w_res) == 3
        w_object_cls = ec.space.getclassfor(W_Object)
        assert "Constant" not in w_object_cls.constants_w

    def test_module_constant(self, ec):
        w_res = ec.space.execute(ec, """
        ExternalConst = 10
        module Y
            Constant = 5
            OtherConstant = ExternalConst
        end
        return [Y::Constant, Y::OtherConstant]
        """)
        assert self.unwrap(ec.space, w_res) == [5, 10]

    def test_subclass_constant(self, ec):
        w_res = ec.space.execute(ec, """
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
        assert [ec.space.int_w(w_x) for w_x in ec.space.listview(w_res)] == [3, 5]

    def test_class_constant_block(self, ec):
        w_res = ec.space.execute(ec, """
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
        assert [ec.space.int_w(w_x) for w_x in ec.space.listview(w_res)] == [5, 5]

    def test_instance_var(self, ec):
        w_res = ec.space.execute(ec, """
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
        assert ec.space.str_w(w_res) == "abc"

    def test_send_block(self, ec):
        w_res = ec.space.execute(ec, """
        res = []
        [1, 2, 3].each do |x|
            res << (x * 2)
        end
        return res
        """)
        assert [ec.space.int_w(w_x) for w_x in ec.space.listview(w_res)] == [2, 4, 6]

    def test_yield(self, ec):
        w_res = ec.space.execute(ec, """
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
        assert [ec.space.int_w(w_x) for w_x in ec.space.listview(w_res)] == [-1, -1]

    def test_range(self, ec):
        w_res = ec.space.execute(ec, "return (1..10).begin")
        assert ec.space.int_w(w_res) == 1
        w_res = ec.space.execute(ec, "return (1...10).end")
        assert ec.space.int_w(w_res) == 10

    def test_augmented_assignment(self, ec):
        w_res = ec.space.execute(ec, "i = 0; i += 5; return i")
        assert ec.space.int_w(w_res) == 5
        w_res = ec.space.execute(ec, """
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
        assert ec.space.int_w(w_res) == 10

        w_res = ec.space.execute(ec, """
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
        assert ec.space.int_w(w_res) == 3

    def test_or_equal(self, ec):
        w_res = ec.space.execute(ec, """
        x = nil
        x ||= 5
        v = x
        x ||= 3
        return [v, x]
        """)
        assert self.unwrap(ec.space, w_res) == [5, 5]
        w_res = ec.space.execute(ec, """
        x = [nil]
        x[0] ||= 5
        return x
        """)
        assert self.unwrap(ec.space, w_res) == [5]

    def test_lookup_constant(self, ec):
        w_res = ec.space.execute(ec, """
        class X
            Constant = 3
        end
        return X::Constant
        """)
        assert ec.space.int_w(w_res) == 3

    def test___FILE__(self, ec):
        w_res = ec.space.execute(ec, "return __FILE__")
        assert ec.space.str_w(w_res) == "-e"

    def test_default_arguments(self, ec):
        w_res = ec.space.execute(ec, """
        def f(a, b=3, c=b)
            [a, b, c]
        end
        return f 1
        """)
        assert [ec.space.int_w(w_x) for w_x in ec.space.listview(w_res)] == [1, 3, 3]
        w_res = ec.space.execute(ec, "return f 5, 6")
        assert [ec.space.int_w(w_x) for w_x in ec.space.listview(w_res)] == [5, 6, 6]
        w_res = ec.space.execute(ec, "return f 5, 6, 10")
        assert [ec.space.int_w(w_x) for w_x in ec.space.listview(w_res)] == [5, 6, 10]

    def test_module(self, ec):
        w_res = ec.space.execute(ec, """
        module M
            def method
                5
            end
        end
        return M
        """)
        assert isinstance(w_res, W_ModuleObject)
        assert w_res.name == "M"

        with self.raises("NoMethodError"):
            ec.space.execute(ec, "M.method")

    def test_singleton_method(self, ec):
        w_res = ec.space.execute(ec, """
        def Array.hello
            "hello world"
        end

        return Array.hello
        """)
        assert ec.space.str_w(w_res) == "hello world"

        with self.raises("NoMethodError"):
            ec.space.execute(ec, "[].hello")

    def test_splat(self, ec):
        w_res = ec.space.execute(ec, """
        def f(a, b, c, d, e, f)
            [a, b, c, d, e, f]
        end

        return f(*2, *[5, 3], *[], 7, 8, *[1], *nil)
        """)
        assert [ec.space.int_w(w_x) for w_x in ec.space.listview(w_res)] == [2, 5, 3, 7, 8, 1]

        w_res = ec.space.execute(ec, """
        class ToA
            def to_a
                [1, 2, 3, 4, 5, 6]
            end
        end

        return f *ToA.new
        """)
        assert [ec.space.int_w(w_x) for w_x in ec.space.listview(w_res)] == [1, 2, 3, 4, 5, 6]

        w_res = ec.space.execute(ec, """
        class ToAry
            def to_ary
                [1, 5, 6, 7, 8, 9]
            end
        end

        return f *ToAry.new
        """)
        assert [ec.space.int_w(w_x) for w_x in ec.space.listview(w_res)] == [1, 5, 6, 7, 8, 9]

    def test_send_block_splat(self, ec):
        w_res = ec.space.execute(ec, """
        def f(a)
            x = yield
            return a + x
        end

        return f(*2) { 5 }
        """)
        assert ec.space.int_w(w_res) == 7

    def test_global_variables(self, ec):
        w_res = ec.space.execute(ec, "return $abc")
        assert w_res is ec.space.w_nil
        w_res = ec.space.execute(ec, "$abc = 3; return $abc")
        assert ec.space.int_w(w_res) == 3

    def test_assign_constant(self, ec):
        w_res = ec.space.execute(ec, """
        class X
        end
        X::Constant = 5
        return X::Constant
        """)
        assert ec.space.int_w(w_res) == 5
        with self.raises("NameError"):
            ec.space.execute(ec, "Constant")

    def test_receive_splat_argument(self, ec):
        w_res = ec.space.execute(ec, """
        def f(*args)
            args
        end

        return f(1, 2, *[3, 4])
        """)
        assert self.unwrap(ec.space, w_res) == [1, 2, 3, 4]

    def test_or(self, ec):
        w_res = ec.space.execute(ec, "return 3 + 4 || 5")
        assert ec.space.int_w(w_res) == 7
        w_res = ec.space.execute(ec, "return nil || 12")
        assert ec.space.int_w(w_res) == 12

    def test_not(self, ec):
        w_res = ec.space.execute(ec, "return !3")
        assert w_res is ec.space.w_false
        w_res = ec.space.execute(ec, "return !!3")
        assert w_res is ec.space.w_true

    def test_subscript_assignment(self, ec):
        w_res = ec.space.execute(ec, """
        x = [0]
        x[0] = 5
        return x[0]
        """)
        assert ec.space.int_w(w_res) == 5
        w_res = ec.space.execute(ec, """
        x = [0]
        x[0] += 2
        return x[0]
        """)
        assert ec.space.int_w(w_res) == 2

    def test_empty_hash(self, ec):
        ec.space.execute(ec, "return {}")

    def test_multiple_assignment(self, ec):
        w_res = ec.space.execute(ec, """
        a = [3]
        a[0], Object::Const, b = [5, 4]
        return [a, Object::Const, b]
        """)
        assert self.unwrap(ec.space, w_res) == [[5], 4, None]

    def test_splat_lhs_assignment(self, ec):
        w_res = ec.space.execute(ec, """
        a, *b, c = *[1,2]
        return [a, b, c]
        """)
        assert self.unwrap(ec.space, w_res) == [1, [], 2]
        w_res = ec.space.execute(ec, """
        a, *b, c = 1,2,3,4
        return [a, b, c]
        """)
        assert self.unwrap(ec.space, w_res) == [1, [2,3], 4]
        w_res = ec.space.execute(ec, """
        a, *b, c = 1
        return [a, b, c]
        """)
        assert self.unwrap(ec.space, w_res) == [1, [], None]

    def test_minus(self, ec):
        w_res = ec.space.execute(ec, """
        def a(x)
            Math.sin(x)
        end
        b = 1
        c = 1
        return [(a -b), (c -b)]
        """)
        assert self.unwrap(ec.space, w_res) == [math.sin(-1), 0]

    def test_case(self, ec):
        w_res = ec.space.execute(ec, """
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
        assert self.unwrap(ec.space, w_res) == [0, 0, 1, 2]

    def test_dynamic_string(self, ec):
        w_res = ec.space.execute(ec, """
        x = 123
        return "abc, #{x}, easy"
        """)
        assert ec.space.str_w(w_res) == "abc, 123, easy"

    def test_dynamic_regexp(self, ec):
        w_res = ec.space.execute(ec, """
        x = 123
        return /#{x}/.source
        """)
        assert ec.space.str_w(w_res) == "123"


class TestBlocks(BaseRuPyPyTest):
    def test_self(self, ec):
        w_res = ec.space.execute(ec, """
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
        assert [ec.space.int_w(w_x) for w_x in ec.space.listview(w_res)] == [2, 4, 6]

    def test_param_is_cell(self, ec):
        w_res = ec.space.execute(ec, """
        def sum(arr, start)
            arr.each do |x|
                start += x
            end
            start
        end

        return sum([1, 2, 3], 4)
        """)
        assert ec.space.int_w(w_res) == 10

    def test_nested_block(self, ec):
        w_res = ec.space.execute(ec, """
        result = []
        [1, 2, 3].each do |x|
            [3, 4, 5].each do |y|
                result << x - y
            end
        end
        return result
        """)
        assert [ec.space.int_w(w_x) for w_x in ec.space.listview(w_res)] == [-2, -3, -4, -1, -2, -3, 0, -1, -2]

    def test_no_accepted_arguments(self, ec):
        w_res = ec.space.execute(ec, """
        result = []
        2.times do
            result << "hello"
        end
        return result
        """)
        assert [ec.space.str_w(w_x) for w_x in ec.space.listview(w_res)] == ["hello", "hello"]

    def test_multi_arg_block_array(self, ec):
        w_res = ec.space.execute(ec, """
        res = []
        [[1, 2], [3, 4]].each do |x, y|
            res << x - y
        end
        return res
        """)
        assert [ec.space.int_w(w_x) for w_x in ec.space.listview(w_res)] == [-1, -1]

    def test_block_argument(self, ec):
        w_res = ec.space.execute(ec, """
        def f(&b)
            b.call
        end
        return f { 5 }
        """)
        assert ec.space.int_w(w_res) == 5

        w_res = ec.space.execute(ec, """
        def g(&b)
            b
        end
        return g
        """)
        assert w_res is ec.space.w_nil

        w_res = ec.space.execute(ec, """
        def h(&b)
            [1, 2, 3].map { |x| b.call(x) }
        end
        return h { |x| x * 3 }
        """)
        assert [ec.space.int_w(w_x) for w_x in ec.space.listview(w_res)] == [3, 6, 9]

    def test_block_argument_send(self, ec):
        w_res = ec.space.execute(ec, """
        f = lambda { |x| x * 2 }
        return [1, 2, 3].map(&f)
        """)
        assert self.unwrap(ec.space, w_res) == [2, 4, 6]
        w_res = ec.space.execute(ec, """
        def x(&b)
            b
        end
        return x(&nil)
        """)
        assert w_res is ec.space.w_nil

        with self.raises("TypeError"):
            ec.space.execute(ec, "f(&3)")

    def test_block_return(self, ec):
        w_res = ec.space.execute(ec, """
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
        assert ec.space.int_w(w_res) == 15


class TestExceptions(BaseRuPyPyTest):
    def test_simple(self, ec):
        w_res = ec.space.execute(ec, """
        return begin
            1 / 0
        rescue ZeroDivisionError
            5
        end
        """)
        assert ec.space.int_w(w_res) == 5

    def test_bind_to_name(self, ec):
        w_res = ec.space.execute(ec, """
        return begin
            1 / 0
        rescue ZeroDivisionError => e
            e.to_s
        end
        """)
        assert ec.space.str_w(w_res) == "divided by 0"

    def test_rescue_no_exception(self, ec):
        w_res = ec.space.execute(ec, """
        return begin
            1 + 1
        rescue ZeroDivisionError
            5
        end
        """)
        assert ec.space.int_w(w_res) == 2

    def test_uncaught_exception(self, ec):
        with self.raises("NoMethodError"):
            ec.space.execute(ec, """
            begin
                [].dsafdsafsa
            rescue ZeroDivisionError
                5
            end
            """)

    def test_multiple_rescues(self, ec):
        w_res = ec.space.execute(ec, """
        return begin
            1 / 0
        rescue NoMethodError
            5
        rescue ZeroDivisionError
            10
        end
        """)
        assert ec.space.int_w(w_res) == 10

    def test_nested_rescue(self, ec):
        w_res = ec.space.execute(ec, """
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
        assert ec.space.int_w(w_res) == 5

    def test_simple_ensure(self, ec):
        w_res = ec.space.execute(ec, """
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
        assert [ec.space.int_w(w_x) for w_x in ec.space.listview(w_res)] == [1, 2, 3]

    def test_ensure_return(self, ec):
        w_res = ec.space.execute(ec, """
        res = []
        begin
            return res
        ensure
            res << 1
        end
        """)
        assert [ec.space.int_w(w_x) for w_x in ec.space.listview(w_res)] == [1]

    def test_ensure_block_return(self, ec):
        w_res = ec.space.execute(ec, """
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
        assert self.unwrap(ec.space, w_res) == [12, 5]

    def test_rescue_loop(self, ec):
        w_res = ec.space.execute(ec, """
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
        assert ec.space.int_w(w_res) == 3
