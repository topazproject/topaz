import os

import pytest

from topaz.objects.ioobject import W_IOObject

from ..base import BaseTopazTest


class TestIO(BaseTopazTest):
    def test_constants(self, space):
        assert space.int_w(space.execute("return IO::SEEK_CUR")) == os.SEEK_CUR
        assert space.int_w(space.execute("return IO::SEEK_END")) == os.SEEK_END
        assert space.int_w(space.execute("return IO::SEEK_SET")) == os.SEEK_SET

    def test_new_from_file(self, space, tmpdir):
        contents = "foo\nbar\nbaz\n"
        f = tmpdir.join("file.txt")
        f.write(contents)

        w_res = space.execute("""
        f = File.new('%s')
        io = IO.new(f)
        return io.read
        """ % f)
        assert space.str_w(w_res) == contents

    def test_new_from_fd(self, space):
        w_res = space.execute("return IO.new(1)")
        assert isinstance(w_res, W_IOObject)

    def test_write(self, space, capfd, tmpdir):
        content = "foo\n"
        space.execute('return IO.new(1, "w").write("%s")' % content)
        out, err = capfd.readouterr()
        assert out == content
        content = "foo\n"

        f = tmpdir.join("file.txt")
        with self.raises(space, "IOError", "closed stream"):
            space.execute("""
            io = File.new('%s', "w")
            io.close
            io.write("")
            """ % f)

    def test_push(self, space, capfd, tmpdir):
        space.execute('return IO.new(1, "w") << "hello" << "world"')
        out, err = capfd.readouterr()
        assert out == "helloworld"

        f = tmpdir.join("file.txt")
        with self.raises(space, "IOError", "closed stream"):
            space.execute("""
            io = File.new('%s', "w")
            io.close
            io << ""
            """ % f)

    def test_read(self, space, tmpdir):
        contents = "foo\nbar\nbaz\n"
        f = tmpdir.join("file.txt")
        f.write(contents)

        w_res = space.execute("return File.new('%s').read" % f)
        assert space.str_w(w_res) == contents

        w_res = space.execute("return File.new('%s').read(4)" % f)
        assert space.str_w(w_res) == contents[:4]

        w_res = space.execute("""
        a = 'hello world'
        File.new('%s').read(10, a)
        return a
        """ % f)
        assert space.str_w(w_res) == contents[:10]

        with self.raises(space, "ArgumentError"):
            space.execute("File.new('%s').read(-1)" % f)

        with self.raises(space, "IOError", "closed stream"):
            space.execute("""
            io = File.new('%s')
            io.close
            io.read
            """ % f)

    def test_simple_print(self, space, capfd, tmpdir):
        space.execute('IO.new(1, "w").print("foo")')
        out, err = capfd.readouterr()
        assert out == "foo"

        f = tmpdir.join("file.txt")
        with self.raises(space, "IOError", "closed stream"):
            space.execute("""
            io = File.new('%s', "w")
            io.close
            io.print ""
            """ % f)

    def test_multi_print(self, space, capfd):
        space.execute('IO.new(1, "w").print("This", "is", 100, "percent")')
        out, err = capfd.readouterr()
        assert out == "Thisis100percent"

    def test_print_globals(self, space, capfd):
        space.globals.set(space, "$,", space.newstr_fromstr(":"))
        space.globals.set(space, "$\\", space.newstr_fromstr("\n"))
        space.execute('IO.new(1, "w").print("foo", "bar", "baz")')
        space.globals.set(space, "$_", space.newstr_fromstr('lastprint'))
        space.execute('IO.new(1, "w").print')
        out, err = capfd.readouterr()
        assert out == "foo:bar:baz\nlastprint\n"

    def test_non_string_print_globals(self, space, capfd):
        space.globals.set(space, "$,", space.w_nil)
        space.globals.set(space, "$\\", space.w_nil)
        space.execute('IO.new(1, "w").print("foo", "bar", "baz")')
        space.globals.set(space, "$_", space.w_nil)
        space.execute('IO.new(1, "w").print')
        out, err = capfd.readouterr()
        assert out == "foobarbaz"

    def test_puts(self, space, capfd, tmpdir):
        space.execute("IO.new(1, 'w').puts('This', 'is\n', 100, 'percent')")
        out, err = capfd.readouterr()
        assert out == "This\nis\n100\npercent\n"

        f = tmpdir.join("file.txt")
        with self.raises(space, "IOError", "closed stream"):
            space.execute("""
            io = File.new('%s', "w")
            io.close
            io.puts ""
            """ % f)

    def test_flush(self, space, capfd, tmpdir):
        space.execute("IO.new(1, 'w').flush.puts('String')")
        out, err = capfd.readouterr()
        assert out == "String\n"

        f = tmpdir.join("file.txt")
        with self.raises(space, "IOError", "closed stream"):
            space.execute("""
            io = File.new('%s', "w")
            io.close
            io.flush
            """ % f)

    def test_globals(self, space, capfd):
        w_res = space.execute("""
        STDOUT.puts("STDOUT")
        $stdout.puts("$stdout")
        $>.puts("$>")
        STDERR.puts("STDERR")
        $stderr.puts("$stderr")
        return STDIN.read, $stdin.read
        """)
        out, err = capfd.readouterr()
        assert out == "STDOUT\n$stdout\n$>\n"
        assert err == "STDERR\n$stderr\n"
        assert self.unwrap(space, w_res) == [None, None]

    def test_rewind(self, space, tmpdir):
        f = tmpdir.join("file.txt")
        f.write("content")
        w_res = space.execute("""
        f = File.new('%s', "r+")
        c = f.read
        f.rewind
        return c, f.read
        """ % f)
        assert self.unwrap(space, w_res) == ["content", "content"]
        with self.raises(space, "IOError", "closed stream"):
            space.execute("""
            io = File.new('%s')
            io.close
            io.rewind
            """ % f)

    def test_seek(self, space, tmpdir):
        f = tmpdir.join("file.txt")
        f.write("content")
        w_res = space.execute("""
        res = []
        f = File.new('%s', "r+")
        f.seek(2, IO::SEEK_SET)
        res << f.read
        f.seek(2)
        res << f.read
        f.seek(-3, IO::SEEK_CUR)
        res << f.read
        f.seek(-2, IO::SEEK_END)
        res << f.read
        return res
        """ % f)
        assert self.unwrap(space, w_res) == [
            "ntent", "ntent", "ent", "nt"
        ]
        with self.raises(space, "IOError", "closed stream"):
            space.execute("""
            io = File.new('%s')
            io.close
            io.seek 2
            """ % f)

    def test_pos(self, space, tmpdir):
        f = tmpdir.join("file.txt")
        f.write("words in here")
        w_res = space.execute("""
        f = File.new('%s', "r+")
        f.seek(2, IO::SEEK_SET)
        pos0 = f.pos
        f.seek(8, IO::SEEK_SET)
        return pos0, f.pos
        """ % f)
        assert self.unwrap(space, w_res) == [2, 8]

    def test_pipe(self, space):
        w_res = space.execute("""
        return IO.pipe
        """)
        w_read, w_write = space.listview(w_res)
        assert isinstance(w_read, W_IOObject)
        assert isinstance(w_read, W_IOObject)
        w_res = space.execute("""
        r, w, r_c, w_c = IO.pipe do |r, w|
          r.close
          [r, w, r.closed?, w.closed?]
        end
        return r.closed?, w.closed?, r_c, w_c
        """)
        assert self.unwrap(space, w_res) == [True, True, True, False]

    def test_singleton_readlines(self, space, tmpdir):
        tmpdir.join("x.txt").write("abc")
        w_res = space.execute("return IO.readlines('%s')" % tmpdir.join("x.txt"))
        assert self.unwrap(space, w_res) == ["abc"]

    def test_to_io(self, space, tmpdir):
        f = tmpdir.join("file.txt")
        f.write("")
        w_res = space.execute("""
        f = File.new '%s'
        return f.eql? f.to_io
        """ % f)
        assert w_res == space.w_true

    def test_to_i(self, space, tmpdir):
        f1 = tmpdir.join("file1.txt")
        f1.write("")
        f2 = tmpdir.join("file2.txt")
        f2.write("")

        w_res = space.execute("""
        f1 = File.new '%s'
        f2 = File.new '%s'
        return f1.to_i, f2.to_i
        """ % (f1, f2))
        fds = self.unwrap(space, w_res)
        assert fds[0] != fds[1]

        w_res = space.execute("return STDIN.to_i")
        assert space.int_w(w_res) == 0
        w_res = space.execute("return STDOUT.to_i")
        assert space.int_w(w_res) == 1
        w_res = space.execute("return STDERR.to_i")
        assert space.int_w(w_res) == 2

    def test_reopen_stdout_in_closed_io(self, space, tmpdir):
        f = tmpdir.join("file.txt")
        f.write('')
        with self.raises(space, "IOError", "closed stream"):
            space.execute("""
            f = File.new('%s')
            f.close
            f.reopen($stdout)
            """ % f)

    def test_reopen_closed_io(self, space, tmpdir):
        f = tmpdir.join("file.txt")
        f.write('')
        with self.raises(space, "IOError", "closed stream"):
            space.execute("""
            f = File.new('%s')
            f.close
            $stderr.reopen(f)
            """ % f)

    def test_reopen(self, space, tmpdir):
        content = "This is line one"
        f = tmpdir.join("testfile")
        f.write(content + "\n")
        w_res = space.execute("""
        res = []
        class A
          def to_io
            File.new("%s")
          end
        end
        f1 = A.new
        f2 = File.new("%s")
        res << f2.readlines[0]
        f2.reopen(f1)
        res << f2.readlines[0]
        res << f2.readlines[0]
        return res
        """ % (f, f))
        assert self.unwrap(space, w_res) == [content, content, ""]

    def test_reopen_path(self, space, tmpdir):
        content = "This is line one"
        f = tmpdir.join("testfile")
        f.write(content + "\n")
        w_res = space.execute("""
        res = []
        f = File.new("%s")
        res << f.readlines[0]
        f.reopen("%s")
        res << f.readlines[0]
        res << f.readlines[0]
        return res
        """ % (f, f))
        assert self.unwrap(space, w_res) == [content, content, ""]

    def test_reopen_with_invalid_arg(self, space):
        with self.raises(space, "TypeError", "can't convert Fixnum into String"):
            space.execute("$stderr.reopen(12)")

    def test_popen_read(self, space):
        w_res = space.execute("""
        io = IO.popen("echo foo", "r")
        return io.pid.is_a?(Fixnum), io.read
        """)
        assert self.unwrap(space, w_res) == [True, "foo\n"]

    @pytest.mark.xfail
    def test_popen_write(self, space, capfd):
        space.execute("""
        IO.popen("cat", "w") do |io|
          io.write 'foo\n'
        end
        """)
        out, err = capfd.readouterr()
        assert out == "foo\n"
