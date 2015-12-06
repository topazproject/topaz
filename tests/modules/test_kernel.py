import os
import time

import pytest

from ..base import BaseTopazTest


class TestKernel(BaseTopazTest):
    def test_puts_nil(self, space, capfd):
        space.execute("puts nil")
        out, err = capfd.readouterr()
        assert out == "\n"

    def test_print(self, space, capfd):
        space.execute("print 1, 3")
        out, err = capfd.readouterr()
        assert out == "13"

    def test_p(self, space, capfd):
        space.execute("p 1,2,3")
        out, err = capfd.readouterr()
        assert out == "1\n2\n3\n"

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
        with self.raises(space, "RuntimeError"):
            space.execute("raise")

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

    def test_Integer(self, space):
        w_res = space.execute("return [Integer(4), Integer('123')]")
        assert self.unwrap(space, w_res) == [4, 123]

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

    def test_eqlp(self, space):
        w_res = space.execute("""
        x = Object.new
        return [x.eql?(x), x.eql?(4)]
        """)
        assert self.unwrap(space, w_res) == [True, False]

    def test_eval(self, space):
        w_res = space.execute("""
        a = 4
        return eval('a + 2')
        """)
        assert space.int_w(w_res) == 6

    def test_responds_to(self, space):
        w_res = space.execute("return [4.respond_to?(:foo_bar), nil.respond_to?(:object_id)]")
        assert self.unwrap(space, w_res) == [False, True]

    def test_Float(self, space):
        assert space.float_w(space.execute("return Float(1)")) == 1.0
        assert space.float_w(space.execute("return Float(1.1)")) == 1.1
        assert space.float_w(space.execute("return Float('1.1')")) == 1.1
        assert space.float_w(space.execute("return Float('1.1e10')")) == 11000000000.0
        with self.raises(space, "TypeError"):
            space.execute("Float(nil)")
        with self.raises(space, "ArgumentError"):
            space.execute("Float('a')")
        w_res = space.execute("""
        class A; def to_f; 1.1; end; end
        return Float(A.new)
        """)
        assert space.float_w(w_res) == 1.1

    def test_loop(self, space):
        w_res = space.execute("""
        res = []
        i = 0
        loop {
          i += 1
          res << i
          break if i == 3
        }
        return res
        """)
        assert self.unwrap(space, w_res) == [1, 2, 3]

    def test_sleep(self, space):
        now = time.time()
        w_res = space.execute("return sleep 0.001")
        assert space.int_w(w_res) == 0
        assert time.time() - now >= 0.001

        now = time.time()
        w_res = space.execute("return sleep 0.002")
        assert space.int_w(w_res) == 0
        assert time.time() - now >= 0.002

        with self.raises(space, "TypeError"):
            space.execute("return sleep nil")
        with self.raises(space, "TypeError"):
            space.execute("return sleep '1'")
        with self.raises(space, "TypeError"):
            space.execute("return sleep Object.new")

    def test_trust(self, space):
        w_res = space.execute("return 'a'.untrusted?")
        assert self.unwrap(space, w_res) is False
        w_res = space.execute("""
        a = 'a'
        a.untrust
        return a.untrusted?, a.dup.untrusted?, a.clone.untrusted?
        """)
        assert self.unwrap(space, w_res) == [True, True, True]
        w_res = space.execute("""
        a = 'a'
        a.untrust
        a.trust
        return a.untrusted?, a.dup.untrusted?, a.clone.untrusted?
        """)
        assert self.unwrap(space, w_res) == [False, False, False]

    def test_taint(self, space):
        w_res = space.execute("return 'a'.tainted?")
        assert self.unwrap(space, w_res) is False
        w_res = space.execute("""
        a = 'a'
        a.taint
        return a.tainted?, a.dup.tainted?, a.clone.tainted?
        """)
        assert self.unwrap(space, w_res) == [True, True, True]
        w_res = space.execute("""
        a = 'a'
        a.taint
        a.untaint
        return a.tainted?, a.dup.tainted?, a.clone.tainted?
        """)
        assert self.unwrap(space, w_res) == [False, False, False]

    def test_freeze(self, space):
        w_res = space.execute("return 'a'.frozen?")
        assert self.unwrap(space, w_res) is False
        w_res = space.execute("""
        a = 'a'
        a.freeze
        return a.frozen?, a.dup.frozen?, a.clone.frozen?
        """)
        assert self.unwrap(space, w_res) == [True, False, True]

    def test_backtick(self, space):
        w_res = space.execute("return `echo 10`")
        assert self.unwrap(space, w_res) == "10\n"

    def test_backtick_sets_process_status(self, space):
        w_res = space.execute("""
        $? = nil
        `echo`
        return $?.class.name
        """)
        assert self.unwrap(space, w_res) == "Process::Status"


class TestRequire(BaseTopazTest):
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
        """ % f)
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
        $LOAD_PATH[0..-1] = ['%s']
        require 't.rb'

        return t(2, 5)
        """ % tmpdir)
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
        """ % (f, f, f))
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
        """ % (f, f, f))
        assert space.int_w(w_res) == 3

    def test_no_ext_on_path(self, space, tmpdir):
        f = tmpdir.join("t.txt")
        f.write("""
        @a = 5
        """)

        w_res = space.execute("""
        require '%s'
        return @a
        """ % f)
        assert space.int_w(w_res) == 5

    def test_null_bytes(self, space):
        with self.raises(space, "ArgumentError", "string contains null byte"):
            space.execute('require "b\\0"')
        with self.raises(space, "ArgumentError", "string contains null byte"):
            space.execute("""
            $LOAD_PATH.unshift "\\0"
            require 'pp'
            """)

    def test_load_path_element_coerce(self, space, tmpdir):
        f = tmpdir.join("t.rb")
        f.write("""
        $success = true
        """)
        w_res = space.execute("""
        class A
          def to_path
            "%s"
          end
        end
        $LOAD_PATH.unshift A.new
        require 't'
        return $success
        """ % tmpdir)
        assert w_res is space.w_true

    def test_path_ambigious_directory_file(self, space, tmpdir):
        f = tmpdir.join("t.rb")
        f.write("""
        $success = true
        """)
        tmpdir.join("t").ensure(dir=True)
        w_res = space.execute("""
        $LOAD_PATH << '%s'
        require '%s'
        return $success
        """ % (tmpdir, tmpdir.join("t")))
        assert w_res is space.w_true


class TestExec(BaseTopazTest):
    def fork_and_wait(self, space, capfd, code):
        cpid = os.fork()
        if cpid == 0:
            try:
                space.execute(code)
            finally:
                os._exit(0)
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

    @pytest.mark.xfail
    def test_exec_with_path_search(self, space, capfd):
        out = self.fork_and_wait(space, capfd, "exec 'echo', '$0'")
        assert out == "$0\n"

    def test_exec_with_null_bytes(self, space):
        with self.raises(space, "ArgumentError", "string contains null byte"):
            space.execute('exec "\\0"')
        with self.raises(space, "ArgumentError", "string contains null byte"):
            space.execute('exec ["\\0", "none"]')
        with self.raises(space, "ArgumentError", "string contains null byte"):
            space.execute('exec ["none", "\\0"]')
        with self.raises(space, "ArgumentError", "string contains null byte"):
            space.execute('exec "none", "\\0"')


class TestSetTraceFunc(BaseTopazTest):
    def test_class(self, space):
        w_res = space.execute("""
        output = []
        set_trace_func proc { |event, file, line, id, binding, classname|
          output << [event, file, line, id, classname]
        }

        class << self
        end

        set_trace_func nil

        return output
        """)
        assert self.unwrap(space, w_res) == [
            ["c-return", "-e", 3, "set_trace_func", "Kernel"],
            ["line", "-e", 7, None, None],
            ["class", "-e", 7, None, None],
            ["end", "-e", 7, None, None],
            ["line", "-e", 10, None, None],
            ["c-call", "-e", 10, "set_trace_func", "Kernel"]
        ]
