import os
import stat

from rupypy.objects.fileobject import W_FileObject, W_IOObject

from ..base import BaseRuPyPyTest


class TestIO(BaseRuPyPyTest):
    def test_new_from_file(self, space, tmpdir):
        contents = "foo\nbar\nbaz\n"
        f = tmpdir.join("file.txt")
        f.write(contents)

        w_res = space.execute("""
        f = File.new('%s')
        io = IO.new(f)
        return io.read
        """ % str(f))
        assert space.str_w(w_res) == contents

    def test_new_from_fd(self, space):
        w_res = space.execute("return IO.new(1)")
        assert isinstance(w_res, W_IOObject)

    def test_write(self, space, capfd):
        content = "foo\n"
        space.execute('return IO.new(1, "w").write("%s")' % content)
        out, err = capfd.readouterr()
        assert out == content
        content = "foo\n"

    def test_push(self, space, capfd):
        space.execute('return IO.new(1, "w") << "hello" << "world"')
        out, err = capfd.readouterr()
        assert out == "helloworld"

    def test_read(self, space, tmpdir):
        contents = "foo\nbar\nbaz\n"
        f = tmpdir.join("file.txt")
        f.write(contents)

        w_res = space.execute("return File.new('%s').read" % str(f))
        assert space.str_w(w_res) == contents

        w_res = space.execute("return File.new('%s').read(4)" % str(f))
        assert space.str_w(w_res) == contents[:4]

        w_res = space.execute("""
        a = 'hello world'
        File.new('%s').read(10, a)
        return a
        """ % str(f))
        assert space.str_w(w_res) == contents[:10]

        with self.raises(space, "ArgumentError"):
            space.execute("return File.new('%s').read(-1)" % str(f))

    def test_gets(self, space, tmpdir):
        contents = "\nfoo\n\nbar"
        f = tmpdir.join("file.txt")
        f.write(contents)

        w_res = space.execute("f = File.new('%s'); return (1..6).map {|i| f.gets}" % str(f))
        lines_w = space.listview(w_res)
        assert [space.str_w(w_s) for w_s in lines_w[:4]] \
            == ['\n', 'foo\n', '\n', 'bar']
        assert lines_w[4:] == [space.w_nil, space.w_nil]

    def test_simple_print(self, space, capfd):
        space.execute('IO.new(1, "w").print("foo")')
        out, err = capfd.readouterr()
        assert out == "foo"

    def test_multi_print(self, space, capfd):
        space.execute('IO.new(1, "w").print("This", "is", 100, "percent")')
        out, err = capfd.readouterr()
        assert out == "Thisis100percent"

    def test_print_globals(self, space, capfd):
        space.globals.set("$,", space.newstr_fromstr(":"))
        space.globals.set("$\\", space.newstr_fromstr("\n"))
        space.execute('IO.new(1, "w").print("foo", "bar", "baz")')
        space.globals.set("$_", space.newstr_fromstr('lastprint'))
        space.execute('IO.new(1, "w").print')
        out, err = capfd.readouterr()
        assert out == "foo:bar:baz\nlastprint\n"

    def test_puts(self, space, capfd):
        space.execute("IO.new(1, 'w').puts('This', 'is\n', 100, 'percent')")
        out, err = capfd.readouterr()
        assert out == "This\nis\n100\npercent\n"

    def test_flush(self, space, capfd):
        space.execute("IO.new(1, 'w').flush.puts('String')")
        out, err = capfd.readouterr()
        assert out == "String\n"

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


class TestFile(BaseRuPyPyTest):
    def test_access_flags(self, space):
        assert space.int_w(space.execute("return File::RDONLY")) == os.O_RDONLY
        assert space.int_w(space.execute("return File::WRONLY")) == os.O_WRONLY
        assert space.int_w(space.execute("return File::RDWR")) == os.O_RDWR
        assert space.int_w(space.execute("return File::APPEND")) == os.O_APPEND
        assert space.int_w(space.execute("return File::CREAT")) == os.O_CREAT
        assert space.int_w(space.execute("return File::EXCL")) == os.O_EXCL
        assert space.int_w(space.execute("return File::TRUNC")) == os.O_TRUNC

    def test_separator(self, space):
        space.execute("File::SEPARATOR")

    def test_alt_separator(self, space):
        space.execute("File::ALT_SEPARATOR")

    def test_fnm_syscase(self, space):
        space.execute("File::FNM_SYSCASE")

    def test_new_simple(self, space, tmpdir):
        contents = "foo\nbar\nbaz\n"
        f = tmpdir.join("file.txt")
        f.write(contents)

        w_res = space.execute("return File.new('%s')" % str(f))
        assert isinstance(w_res, W_FileObject)

        w_res = space.execute("return File.new('%s%snonexist', 'w')" % (tmpdir.dirname, os.sep))
        assert isinstance(w_res, W_FileObject)

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
        w_res = space.execute("return File.exist?('%s')" % str(f))
        assert w_res is space.w_true
        w_res = space.execute("return File.exist?('%s')" % str(tmpdir))
        assert w_res is space.w_true
        w_res = space.execute("return File.exist?('no way this exists')")
        assert w_res is space.w_false

    def test_filep(self, space, tmpdir):
        f = tmpdir.join("test.rb")
        f.write("")
        w_res = space.execute("return File.file?('%s')" % str(f))
        assert w_res is space.w_true
        w_res = space.execute("return File.file?('%s')" % str(tmpdir))
        assert w_res is space.w_false
        w_res = space.execute("return File.file?('no way this exists')")
        assert w_res is space.w_false

    def test_executablep(self, space, tmpdir):
        f = tmpdir.join("test.rb")
        f.write("")
        w_res = space.execute("return File.executable?('%s')" % str(f))
        assert w_res is space.w_false
        os.chmod(str(f), stat.S_IEXEC)
        w_res = space.execute("return File.executable?('%s')" % str(f))
        assert w_res is space.w_true

    def test_directoryp(self, space, tmpdir):
        w_res = space.execute("return File.directory?('%s')" % str(tmpdir))
        assert self.unwrap(space, w_res) is True
        w_res = space.execute("return File.directory?('%s')" % str(tmpdir.join("t.rb")))
        assert self.unwrap(space, w_res) is False


class TestExpandPath(BaseRuPyPyTest):
    def test_expand_to_absolute(self, space):
        w_res = space.execute("""
        return [File.expand_path(""), File.expand_path("a"), File.expand_path("a", nil)]
        """)
        assert self.unwrap(space, w_res) == [
            os.getcwd(),
            os.path.join(os.getcwd(), "a"),
            os.path.join(os.getcwd(), "a"),
        ]

    def test_covert_to_absolute_using_provided_base(self, space):
        w_res = space.execute("""return File.expand_path("", "/tmp")""")
        assert self.unwrap(space, w_res) == "/tmp"
        w_res = space.execute("""return File.expand_path("a", "/tmp")""")
        assert self.unwrap(space, w_res) == "/tmp/a"
        w_res = space.execute("""return File.expand_path("../a", "/tmp/xxx")""")
        assert self.unwrap(space, w_res) == "/tmp/a"
        w_res = space.execute("""return File.expand_path(".", "/")""")
        assert self.unwrap(space, w_res) == "/"

    def test_home_expansion(self, space):
        w_res = space.execute("""return File.expand_path("~")""")
        assert self.unwrap(space, w_res) == os.environ["HOME"]
        w_res = space.execute("""return File.expand_path("~", "/tmp/random")""")
        assert self.unwrap(space, w_res) == os.environ["HOME"]
        w_res = space.execute("""return File.expand_path("~/a", "/tmp/random")""")
        assert self.unwrap(space, w_res) == os.path.join(os.environ["HOME"], "a")


class TestDirname(BaseRuPyPyTest):
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
