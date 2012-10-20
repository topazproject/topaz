import os

import py

from ..base import BaseRuPyPyTest


class TestKernel(BaseRuPyPyTest):
    def test_puts_nil(self, space, capfd):
        space.execute("puts nil")
        out, err = capfd.readouterr()
        assert out == "\n"

    def test_print(self, space, capfd):
        space.execute("print 1, 3")
        out, err = capfd.readouterr()
        assert out == "13"

    def test_lambda(self, space):
        w_res = space.execute("""
        l = lambda { |x| 3 }
        return [l.class, l.lambda?]
        """)
        w_cls, w_lambda = space.listview(w_res)
        assert w_cls is space.w_proc
        assert w_lambda is space.w_true

    def test_proc(self, space):
        w_res = space.execute("""
        l = proc { |x| 3 }
        return [l.class, l.lambda?]
        """)
        w_cls, w_lambda = space.listview(w_res)
        assert w_cls is space.w_proc
        assert w_lambda is space.w_false

    def test_singleton_methods(self, space):
        w_res = space.execute("""
        class X
        end

        return X.new.singleton_methods
        """)
        assert self.unwrap(space, w_res) == []

        w_res = space.execute("""
        def X.foo
        end

        return X.singleton_methods
        """)
        assert self.unwrap(space, w_res) == ["foo"]

        w_res = space.execute("""
        class Y < X
        end
        return [Y.singleton_methods, Y.singleton_methods(false)]
        """)
        assert self.unwrap(space, w_res) == [["foo"], []]

    def test_raise(self, space):
        with self.raises(space, "RuntimeError", "foo"):
            space.execute("raise 'foo'")
        with self.raises(space, "TypeError", "foo"):
            space.execute("raise TypeError, 'foo'")
        with self.raises(space, "TypeError", "foo"):
            space.execute("fail TypeError, 'foo'")
        with self.raises(space, "TypeError", "exception class/object expected"):
            space.execute("fail nil")
        with self.raises(space, "TypeError", "exception object expected"):
            space.execute("""
            class A
              def exception(msg=nil)
              end
            end
            raise A.new
            """)
        with self.raises(space, "RuntimeError"):
            space.execute("""
            class A
              def exception(msg=nil); RuntimeError.new(msg); end
            end
            raise A.new
            """)

    def test_overriding_raise(self, space):
        w_res = space.execute("""
        class A
          def raise(*args); args; end
          def do_raise; raise 'foo'; end
        end
        return A.new.do_raise
        """)
        assert self.unwrap(space, w_res) == ['foo']

    def test_raise_error_subclass(self, space):
        with self.raises(space, "CustomError", 'foo'):
            space.execute("""
            class CustomError < StandardError; end
            raise CustomError, 'foo'
            """)

    def test_Array(self, space):
        w_res = space.execute("""
        class A
          def to_ary; ["to_ary"]; end
          def to_a; ["to_a"]; end
        end
        class B
          def to_a; ["to_a"]; end
        end
        return Array(A.new), Array(B.new)
        """)
        assert self.unwrap(space, w_res) == [["to_ary"], ["to_a"]]
        assert self.unwrap(space, space.execute("return Array(1)")) == [1]

    def test_String(self, space):
        w_res = space.execute("return [String('hello'), String(4)]")
        assert self.unwrap(space, w_res) == ["hello", "4"]

    def test_exit(self, space):
        with self.raises(space, "SystemExit"):
            space.execute("Kernel.exit")
        with self.raises(space, "SystemExit"):
            space.execute("exit")

    def test_block_given_p(self, space):
        assert space.execute("return block_given?") is space.w_false
        assert space.execute("return iterator?") is space.w_false
        assert space.execute("return (proc { block_given? })[]") is space.w_false
        w_res = space.execute("""
        def foo
          block_given?
        end
        return foo, foo { }
        """)
        assert self.unwrap(space, w_res) == [False, True]
        w_res = space.execute("""
        def foo
          bar { block_given? }
        end

        def bar
          yield
        end

        return foo, foo { }
        """)
        assert self.unwrap(space, w_res) == [False, True]


class TestRequire(BaseRuPyPyTest):
    def test_simple(self, space, tmpdir):
        f = tmpdir.join("t.rb")
        f.write("""
        def t(a, b)
            a - b
        end
        """)
        w_res = space.execute("""
        require '%s'

        return t(5, 10)
        """ % str(f))
        assert space.int_w(w_res) == -5

    def test_no_ext(self, space, tmpdir):
        f = tmpdir.join("t.rb")
        f.write("""
        def t(a, b)
            a - b
        end
        """)
        w_res = space.execute("""
        require '%s'

        return t(12, 21)
        """ % str(f)[:-3])
        assert space.int_w(w_res) == -9

    def test_load_path(self, space, tmpdir):
        f = tmpdir.join("t.rb")
        f.write("""
        def t(a, b)
            a - b
        end
        """)
        w_res = space.execute("""
        $LOAD_PATH = ['%s']
        require 't.rb'

        return t(2, 5)
        """ % str(tmpdir))
        assert space.int_w(w_res) == -3

    def test_stdlib_default_load_path(self, space):
        w_res = space.execute("""
        return require 'prettyprint'
        """)
        assert w_res is space.w_true

    def test_nonexistance(self, space):
        with self.raises(space, "LoadError"):
            space.execute("require 'xxxxxxx'")

    def test_already_loaded(self, space, tmpdir):
        f = tmpdir.join("f.rb")
        f.write("""
        @a += 1
        """)

        w_res = space.execute("""
        @a = 0
        require '%s'
        require '%s'
        require '%s'

        return @a
        """ % (str(f), str(f), str(f)))
        assert space.int_w(w_res) == 1

    def test_load(self, space, tmpdir):
        f = tmpdir.join("f.rb")
        f.write("""
        @a += 1
        """)

        w_res = space.execute("""
        @a = 0
        load '%s'
        load '%s'
        load '%s'

        return @a
        """ % (str(f), str(f), str(f)))
        assert space.int_w(w_res) == 3

    def test_responds_to(self, space):
        w_res = space.execute("return [4.respond_to?(:foo_bar), nil.respond_to?(:object_id)]")
        assert self.unwrap(space, w_res) == [False, True]


class TestExec(BaseRuPyPyTest):
    def fork_and_wait(self, space, capfd, code):
        cpid = os.fork()
        if cpid == 0:
            space.execute(code)
        else:
            os.waitpid(cpid, 0)
            out, err = capfd.readouterr()
            return out

    def test_exec_with_sh(self, space, capfd):
        out = self.fork_and_wait(space, capfd, "exec 'echo $0'")
        assert out == "sh\n"

    def test_exec_directly(self, space, capfd):
        out = self.fork_and_wait(space, capfd, "exec '/bin/echo', '$0'")
        assert out == "$0\n"

    def test_exec_with_custom_argv0(self, space, capfd):
        out = self.fork_and_wait(space, capfd, "exec ['/bin/sh', 'argv0'], '-c', 'echo $0'")
        assert out == "argv0\n"

    @py.test.mark.xfail
    def test_exec_with_path_search(self, space, capfd):
        out = self.fork_and_wait(space, capfd, "exec 'echo', '$0'")
        assert out == "$0\n"
