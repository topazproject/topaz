import os
import stat

import pytest

from topaz.objects.fileobject import W_FileObject, W_IOObject

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


class TestFile(BaseTopazTest):
    def test_access_flags(self, space):
        assert space.int_w(space.execute("return File::RDONLY")) == os.O_RDONLY
        assert space.int_w(space.execute("return File::WRONLY")) == os.O_WRONLY
        assert space.int_w(space.execute("return File::RDWR")) == os.O_RDWR
        assert space.int_w(space.execute("return File::APPEND")) == os.O_APPEND
        assert space.int_w(space.execute("return File::CREAT")) == os.O_CREAT
        assert space.int_w(space.execute("return File::EXCL")) == os.O_EXCL
        assert space.int_w(space.execute("return File::TRUNC")) == os.O_TRUNC
        w_res = space.execute("return File::BINARY")
        assert space.int_w(w_res) == (os.O_BINARY if hasattr(os, "O_BINARY") else 0)

    def test_separator(self, space):
        space.execute("File::SEPARATOR")

    def test_alt_separator(self, space):
        space.execute("File::ALT_SEPARATOR")

    def test_path_separator(self, space):
        space.execute("File::PATH_SEPARATOR")

    def test_fnm_syscase(self, space):
        space.execute("File::FNM_SYSCASE")

    def test_fnm_dotmatch(self, space):
        space.execute("File::FNM_DOTMATCH")

    def test_fnm_pathname(self, space):
        space.execute("File::FNM_PATHNAME")

    def test_fnm_noescape(self, space):
        space.execute("File::FNM_NOESCAPE")

    def test_new_simple(self, space, tmpdir):
        contents = "foo\nbar\nbaz\n"
        f = tmpdir.join("file.txt")
        f.write(contents)

        w_res = space.execute("return File.new('%s')" % f)
        assert isinstance(w_res, W_FileObject)
        w_res = space.execute("return File.new('%s', 'r')" % f)
        assert isinstance(w_res, W_FileObject)
        w_res = space.execute("return File.new('%s', 'rb')" % f)
        assert isinstance(w_res, W_FileObject)
        w_res = space.execute("return File.new('%s', 'r+')" % f)
        assert isinstance(w_res, W_FileObject)
        w_res = space.execute("return File.new('%s', 'rb+')" % f)
        assert isinstance(w_res, W_FileObject)
        w_res = space.execute("return File.new('%s', 'a+')" % f)
        assert isinstance(w_res, W_FileObject)

        with self.raises(space, "ArgumentError", "invalid access mode rw"):
            space.execute("File.new('%s', 'rw')" % f)
        with self.raises(space, "ArgumentError", "invalid access mode wa"):
            space.execute("File.new('%s', 'wa')" % f)
        with self.raises(space, "ArgumentError", "invalid access mode rw+"):
            space.execute("File.new('%s', 'rw+')" % f)
        with self.raises(space, "ArgumentError", "invalid access mode ra"):
            space.execute("File.new('%s', 'ra')" % f)
        with self.raises(space, "SystemCallError"):
            space.execute("File.new('%s', 1)" % tmpdir.join("non-existant"))

        w_res = space.execute("return File.new('%s%snonexist', 'w')" % (tmpdir.dirname, os.sep))
        assert isinstance(w_res, W_FileObject)

        w_res = space.execute("""
        path = '%s%snonexist2'
        f = File.new(path, 'w')
        f.puts "first"
        f = File.new(path, 'a')
        f.puts "second"
        f = File.new(path, 'r')
        return f.read
        """ % (tmpdir.dirname, os.sep))
        assert space.str_w(w_res) == "first\nsecond\n"

    def test_readlines(self, space, tmpdir):
        contents = "01\n02\n03\n04\n"
        f = tmpdir.join("file.txt")
        f.write(contents)
        w_res = space.execute("return File.new('%s').readlines()" % f)
        assert self.unwrap(space, w_res) == ["01", "02", "03", "04", ""]

        w_res = space.execute("return File.new('%s').readlines('3')" % f)
        assert self.unwrap(space, w_res) == ["01\n02\n0", "\n04\n"]

        w_res = space.execute("return File.new('%s').readlines(1)" % f)
        assert self.unwrap(space, w_res) == ["0", "1", "0", "2", "0", "3", "0", "4", ""]

        w_res = space.execute("return File.new('%s').readlines('3', 4)" % f)
        assert self.unwrap(space, w_res) == ["01\n0", "2\n0", "\n04\n"]

    def test_each_line(self, space, tmpdir):
        contents = "01\n02\n03\n04\n"
        f = tmpdir.join("file.txt")
        f.write(contents)
        w_res = space.execute("""
        r = []
        File.new('%s').each_line { |l| r << l }
        return r
        """ % f)
        assert self.unwrap(space, w_res) == ["01", "02", "03", "04", ""]
        w_res = space.execute("""
        r = []
        File.new('%s').each_line('3') { |l| r << l }
        return r
        """ % f)
        assert self.unwrap(space, w_res) == ["01\n02\n0", "\n04\n"]
        w_res = space.execute("""
        r = []
        File.new('%s').each_line(1) { |l| r << l }
        return r
        """ % f)
        assert self.unwrap(space, w_res) == ["0", "1", "0", "2", "0", "3", "0", "4", ""]
        w_res = space.execute("""
        r = []
        File.new('%s').each_line('3', 4) { |l| r << l }
        return r
        """ % f)
        assert self.unwrap(space, w_res) == ["01\n0", "2\n0", "\n04\n"]

        with self.raises(space, "ArgumentError", "invalid limit: 0 for each_line"):
            w_res = space.execute("""
            File.new('%s').each_line(0) { |l| }
            """ % f)

    def test_join(self, space):
        w_res = space.execute("return File.join('/abc', 'bin')")
        assert space.str_w(w_res) == "/abc/bin"
        w_res = space.execute("return File.join")
        assert space.str_w(w_res) == ""
        w_res = space.execute("return File.join('abc')")
        assert space.str_w(w_res) == "abc"
        w_res = space.execute("return File.join('abc', 'def', 'ghi')")
        assert space.str_w(w_res) == "abc/def/ghi"
        w_res = space.execute("return File.join(['abc', ['def'], []], 'ghi')")
        assert space.str_w(w_res) == "abc/def/ghi"
        w_res = space.execute("return File.join('a', '//', 'b', '/', 'd', '/')")
        assert space.str_w(w_res) == "a//b/d/"

    def test_existp(self, space, tmpdir):
        f = tmpdir.join("test.rb")
        f.write("")
        w_res = space.execute("return File.exist?('%s')" % f)
        assert w_res is space.w_true
        w_res = space.execute("return File.exist?('%s')" % tmpdir)
        assert w_res is space.w_true
        w_res = space.execute("return File.exist?('no way this exists')")
        assert w_res is space.w_false

    def test_filep(self, space, tmpdir):
        f = tmpdir.join("test.rb")
        f.write("")
        w_res = space.execute("return File.file?('%s')" % f)
        assert w_res is space.w_true
        w_res = space.execute("return File.file?('%s')" % tmpdir)
        assert w_res is space.w_false
        w_res = space.execute("return File.file?('no way this exists')")
        assert w_res is space.w_false

    def test_executablep(self, space, tmpdir):
        f = tmpdir.join("test.rb")
        f.write("")
        w_res = space.execute("return File.executable?('%s')" % f)
        assert w_res is space.w_false
        os.chmod(str(f), stat.S_IEXEC)
        w_res = space.execute("return File.executable?('%s')" % f)
        assert w_res is space.w_true

    def test_directoryp(self, space, tmpdir):
        w_res = space.execute("return File.directory?('%s')" % tmpdir)
        assert self.unwrap(space, w_res) is True
        w_res = space.execute("return File.directory?('%s')" % tmpdir.join("t.rb"))
        assert self.unwrap(space, w_res) is False

    def test_open(self, space, tmpdir):
        contents = "foo\nbar\nbaz\n"
        f = tmpdir.join("file.txt")
        f.write(contents)

        w_res = space.execute("""
        File.open('%s') { |f| return f, f.read }
        """ % f)
        w_file, w_string = space.listview(w_res)
        assert space.str_w(w_string) == contents
        with pytest.raises(OSError):
            # fd should be inaccessible
            os.fstat(w_file.fd)

    def test_close(self, space, tmpdir):
        f = tmpdir.join("file.txt")
        f.write("")
        w_res = space.execute("""
        f = File.new('%s')
        f.close
        return f
        """ % f)
        with pytest.raises(OSError):
            # fd should be inaccessible
            os.fstat(w_res.fd)

    def test_closedp(self, space, tmpdir):
        f = tmpdir.join("file.txt")
        f.write("")
        w_res = space.execute("""
        f = File.new('%s')
        opened = f.closed?
        f.close
        return opened, f.closed?
        """ % f)
        assert self.unwrap(space, w_res) == [False, True]

    def test_basename(self, space):
        assert space.str_w(space.execute("return File.basename('ab')")) == "ab"
        assert space.str_w(space.execute("return File.basename('/ab')")) == "ab"
        assert space.str_w(space.execute("return File.basename('/foo/bar/ab')")) == "ab"

    def test_truncate(self, space, tmpdir):
        f = tmpdir.join("file.txt")
        f.write("content")
        w_res = space.execute("""
        f = File.new('%s', "r+")
        f.truncate(3)
        return f.read
        """ % f)
        assert self.unwrap(space, w_res) == "con"

    def test_get_umask(self, space, monkeypatch):
        monkeypatch.setattr(os, "umask", lambda mask: 2)
        w_res = space.execute("return File.umask")
        assert space.int_w(w_res) == 2

    def test_set_umask(self, space, monkeypatch):
        umask = [2]

        def mock_umask(mask):
            [current], umask[0] = umask, mask
            return current
        monkeypatch.setattr(os, "umask", mock_umask)
        w_res = space.execute("return File.umask(10), File.umask")
        assert self.unwrap(space, w_res) == [2, 10]


class TestExpandPath(BaseTopazTest):
    def test_expand_to_absolute(self, space):
        w_res = space.execute("""
        return [File.expand_path(""), File.expand_path("a"), File.expand_path("a", nil)]
        """)
        assert self.unwrap(space, w_res) == [
            os.getcwd(),
            os.path.join(os.getcwd(), "a"),
            os.path.join(os.getcwd(), "a"),
        ]
        with self.raises(space, "ArgumentError", "string contains null byte"):
            space.execute("""return File.expand_path(".\\0.")""")

    def test_covert_to_absolute_using_provided_base(self, space):
        w_res = space.execute("""return File.expand_path("", "/tmp")""")
        assert self.unwrap(space, w_res) == "/tmp"
        w_res = space.execute("""return File.expand_path("a", "/tmp")""")
        assert self.unwrap(space, w_res) == "/tmp/a"
        w_res = space.execute("""return File.expand_path("../a", "/tmp/xxx")""")
        assert self.unwrap(space, w_res) == "/tmp/a"
        w_res = space.execute("""return File.expand_path(".", "/")""")
        assert self.unwrap(space, w_res) == "/"
        w_res = space.execute("""return File.expand_path(".", nil)""")
        assert self.unwrap(space, w_res) == os.getcwd()

    def test_home_expansion(self, space):
        w_res = space.execute("""return File.expand_path("~")""")
        assert self.unwrap(space, w_res) == os.environ["HOME"]
        w_res = space.execute("""return File.expand_path("~", "/tmp/random")""")
        assert self.unwrap(space, w_res) == os.environ["HOME"]
        w_res = space.execute("""return File.expand_path("~/a", "/tmp/random")""")
        assert self.unwrap(space, w_res) == os.path.join(os.environ["HOME"], "a")


class TestDirname(BaseTopazTest):
    def test_simple(self, space):
        w_res = space.execute("""
        return [
            File.dirname("/home/guido"),
            File.dirname("/home/guido/test.txt"),
            File.dirname("test.txt"),
            File.dirname("/home///guido//file.txt"),
            File.dirname(""),
            File.dirname("/"),
            File.dirname("/foo/foo")
        ]
        """)
        assert self.unwrap(space, w_res) == [
            "/home",
            "/home/guido",
            ".",
            "/home///guido",
            ".",
            "/",
            "/foo",
        ]
