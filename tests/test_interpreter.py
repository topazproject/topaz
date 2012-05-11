from rupypy.objects.boolobject import W_TrueObject
from rupypy.objects.moduleobject import W_ModuleObject
from rupypy.objects.objectobject import W_Object

from .base import BaseRuPyPyTest


class TestInterpreter(BaseRuPyPyTest):
    def test_add(self, space):
        w_res = space.execute("1 + 1")
        assert isinstance(w_res, W_TrueObject)

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

    def test_return(self, space):
        w_res = space.execute("return 4")
        assert space.int_w(w_res) == 4

    def test_array(self, space):
        w_res = space.execute("return [[1], [2], [3]]")
        assert [[space.int_w(w_y) for w_y in space.listview(w_x)] for w_x in space.listview(w_res)] == [[1], [2], [3]]

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

    def test_interpter(self, space):
        w_res = space.execute('return "abc"')
        assert space.str_w(w_res) == "abc"

        w_res = space.execute("""
        def test
            x = ""
            x << "abc"
        end

        return [test, test]
        """)

        assert [space.str_w(w_s) for w_s in space.listview(w_res)] == ["abc", "abc"]

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
        w_cls = space.getclassfor(W_Object).constants_w["X"]
        assert w_cls.methods.viewkeys() == {"m", "f"}

        w_res = space.execute("""
        class Z < X
            def g
                3
            end
        end

        z = Z.new
        return [z.f, z.g]
        """)
        assert [space.int_w(w_x) for w_x in space.listview(w_res)] == [2, 3]

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
        w_cls = space.getclassfor(W_Object).constants_w["X"]
        assert w_cls.methods.viewkeys() == {"m", "f"}

    def test_constant(self, space):
        w_res = space.execute("Abc = 3; return Abc")
        assert space.int_w(w_res)

        w_object_cls = space.getclassfor(W_Object)
        assert w_object_cls.constants_w["Abc"] is w_res

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
        w_object_cls = space.getclassfor(W_Object)
        assert "Constant" not in w_object_cls.constants_w

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
        assert [space.int_w(w_x) for w_x in space.listview(w_res)] == [3, 5]

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
        assert [space.int_w(w_x) for w_x in space.listview(w_res)] == [5, 5]

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
        assert [space.int_w(w_x) for w_x in space.listview(w_res)] == [2, 4, 6]

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
        assert [space.int_w(w_x) for w_x in space.listview(w_res)] == [-1, -1]

    def test_range(self, space):
        w_res = space.execute("return (1..10).begin")
        assert space.int_w(w_res) == 1
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

    def test_lookup_constant(self, space):
        w_res = space.execute("""
        class X
            Constant = 3
        end
        return X::Constant
        """)
        assert space.int_w(w_res) == 3

    def test___FILE__(self, space):
        w_res = space.execute("return __FILE__")
        assert space.str_w(w_res) == "-e"

    def test_default_arguments(self, space):
        w_res = space.execute("""
        def f(a, b=3, c=b)
            [a, b, c]
        end
        return f 1
        """)
        assert [space.int_w(w_x) for w_x in space.listview(w_res)] == [1, 3, 3]
        w_res = space.execute("return f 5, 6")
        assert [space.int_w(w_x) for w_x in space.listview(w_res)] == [5, 6, 6]
        w_res = space.execute("return f 5, 6, 10")
        assert [space.int_w(w_x) for w_x in space.listview(w_res)] == [5, 6, 10]

    def test_module(self, space):
        w_res = space.execute("""
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
            space.execute("M.method")


class TestBlocks(object):
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
        assert [space.int_w(w_x) for w_x in space.listview(w_res)] == [2, 4, 6]

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
        assert [space.int_w(w_x) for w_x in space.listview(w_res)] == [-2, -3, -4, -1, -2, -3, 0, -1, -2]

    def test_no_accepted_arguments(self, space):
        w_res = space.execute("""
        result = []
        2.times do
            result << "hello"
        end
        return result
        """)
        assert [space.str_w(w_x) for w_x in space.listview(w_res)] == ["hello", "hello"]

    def test_multi_arg_block_array(self, space):
        w_res = space.execute("""
        res = []
        [[1, 2], [3, 4]].each do |x, y|
            res << x - y
        end
        return res
        """)
        assert [space.int_w(w_x) for w_x in space.listview(w_res)] == [-1, -1]

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
        assert [space.int_w(w_x) for w_x in space.listview(w_res)] == [3, 6, 9]

    def test_splat(self, space):
        w_res = space.execute("""
        def f(a, b, c, d, e, f)
            [a, b, c, d, e, f]
        end

        return f(*2, *[5, 3], *[], 7, 8, *[1], *nil)
        """)
        assert [space.int_w(w_x) for w_x in space.listview(w_res)] == [2, 5, 3, 7, 8, 1]

        w_res = space.execute("""
        class ToA
            def to_a
                [1, 2, 3, 4, 5, 6]
            end
        end

        return f *ToA.new
        """)
        assert [space.int_w(w_x) for w_x in space.listview(w_res)] == [1, 2, 3, 4, 5, 6]

        w_res = space.execute("""
        class ToAry
            def to_ary
                [1, 5, 6, 7, 8, 9]
            end
        end

        return f *ToAry.new
        """)
        assert [space.int_w(w_x) for w_x in space.listview(w_res)] == [1, 5, 6, 7, 8, 9]


class TestExceptions(BaseRuPyPyTest):
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
        with self.raises("NoMethodError"):
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
        assert [space.int_w(w_x) for w_x in space.listview(w_res)] == [1, 2, 3]

    def test_ensure_return(self, space):
        w_res = space.execute("""
        res = []
        begin
            return res
        ensure
            res << 1
        end
        """)
        assert [space.int_w(w_x) for w_x in space.listview(w_res)] == [1]

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
