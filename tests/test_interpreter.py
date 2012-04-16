from rupypy.objects.boolobject import W_TrueObject
from rupypy.objects.objectobject import W_Object


class TestInterpreter(object):
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
            i = i + 1
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
        assert [[space.int_w(w_y) for w_y in w_x.items_w] for w_x in w_res.items_w] == [[1], [2], [3]]

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

        assert [space.str_w(w_s) for w_s in w_res.items_w] == ["abc", "abc"]

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
        assert [space.int_w(w_x) for w_x in w_res.items_w] == [2, 3]

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

    def test_send_block(self, space, capfd):
        space.execute("""
        [1, 2, 3].each do |x|
            puts x * 2
        end
        """)
        out, err = capfd.readouterr()
        assert out == "2\n4\n6\n"

    def test_yield(self, space, capfd):
        space.execute("""
        class X
            def f
                yield 2, 3
                yield 4, 5
            end
        end

        X.new.f do |x, y|
            puts x + y
        end
        """)
        out, err = capfd.readouterr()
        assert out == "5\n9\n"

