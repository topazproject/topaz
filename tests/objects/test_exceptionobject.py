from topaz.objects.exceptionobject import W_TypeError

from ..base import BaseTopazTest


class TestExceptionObject(BaseTopazTest):
    def test_name(self, space):
        space.execute("""
        Exception
        LoadError
        SyntaxError
        NameError
        StandardError
        LocalJumpError
        IOError
        IndexError
        RegexpError
        ThreadError
        NotImplementedError
        """)

    def test_new(self, space):
        w_res = space.execute("return TypeError.new")
        assert isinstance(w_res, W_TypeError)
        assert w_res.msg == "TypeError"
        w_res = space.execute("return TypeError.new('msg')")
        assert isinstance(w_res, W_TypeError)
        assert w_res.msg == "msg"
        w_res = space.execute("return TypeError.new(nil)")
        assert isinstance(w_res, W_TypeError)
        assert w_res.msg == "TypeError"

    def test_to_s(self, space):
        w_res = space.execute("return TypeError.new('msg').to_s")
        assert space.str_w(w_res) == "msg"

    def test_exceptions(self, space):
        w_res = space.execute("return TypeError.exception('msg')")
        assert isinstance(w_res, W_TypeError)
        w_res = space.execute("""
        e1 = TypeError.new('msg')
        e2 = e1.exception
        e3 = e1.exception('new msg')
        return [e1, e2, e3]
        """)
        res = space.listview(w_res)
        assert res[0] is res[1]
        assert res[0] is not res[2]

    def test_systemcallerror(self, space):
        w_res = space.execute("return SystemCallError.new('msg', 1).errno")
        assert space.int_w(w_res) == 1

    def test_message(self, space):
        w_res = space.execute("""
        begin
          raise "foo"
        rescue StandardError => e
          return e.message
        end
        """)
        assert self.unwrap(space, w_res) == "foo"

    def test_message_calls_to_s(self, space):
        w_res = space.execute("""
        class X < Exception
          def to_s
            "hi, a message!"
          end
        end
        return X.new.message
        """)
        assert space.str_w(w_res) == "hi, a message!"

    def test_backtrace(self, space):
        w_res = space.execute("""
        def f
          yield
        end
        begin
          f { 1 / 0}
        rescue Exception => e
          return e.backtrace
        end
        """)
        assert self.unwrap(space, w_res) == [
            "-e:6:in `/'",
            "-e:6:in `block in <main>'",
            "-e:3:in `f'",
            "-e:6:in `<main>'"
        ]

    def test_backtrace_complex(self, space):
        w_res = space.execute("""
        def f
          1 / 0
        end


        def g
          begin
            f
          rescue => e
            return e
          end
        end

        def h
          e = g
          nil
          nil
          nil
          nil
          @e = e
        end

        def i
          h
          @e
        end

        return i.backtrace
        """)
        assert self.unwrap(space, w_res) == [
            "-e:3:in `/'",
            "-e:3:in `f'",
            "-e:9:in `g'",
            "-e:16:in `h'",
            "-e:25:in `i'",
            "-e:29:in `<main>'",
        ]
