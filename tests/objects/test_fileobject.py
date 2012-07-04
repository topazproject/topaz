import os

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
        w_res = space.execute('return IO.new(1, "w").write("%s")' % content)
        out, err = capfd.readouterr()
        assert out == content

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


class TestFile(BaseRuPyPyTest):
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
