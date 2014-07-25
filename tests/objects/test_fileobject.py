import os
import stat

import pytest

from topaz.objects.fileobject import W_FileObject
from topaz.system import IS_WINDOWS

from ..base import BaseTopazTest


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
        with self.raises(space, "Errno::ENOENT"):
            space.execute("File.new('%s', 1)" % tmpdir.join("non-existent"))

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

    def test_readline(self, space, tmpdir):
        contents = "01\n02\n03\n04\n"
        f = tmpdir.join("file.txt")
        f.write(contents)
        w_res = space.execute("return File.new('%s').readline" % f)
        assert self.unwrap(space, w_res) == "01\n"

        w_res = space.execute("return File.new('%s').readline('3')" % f)
        assert self.unwrap(space, w_res) == "01\n02\n03"

        w_res = space.execute("return File.new('%s').readline(1)" % f)
        assert self.unwrap(space, w_res) == "0"

        w_res = space.execute("return File.new('%s').readline('3', 4)" % f)
        assert self.unwrap(space, w_res) == "01\n0"

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
        w_res = space.execute("return File.join('', 'abc', 'bin')")
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
        w_res = space.execute("return File.join('a', '')")
        assert space.str_w(w_res) == "a/"
        w_res = space.execute("return File.join('a/')")
        assert space.str_w(w_res) == "a/"
        w_res = space.execute("return File.join('a/', '')")
        assert space.str_w(w_res) == "a/"
        w_res = space.execute("return File.join('a', '/')")
        assert space.str_w(w_res) == "a/"
        w_res = space.execute("return File.join('a/', '/')")
        assert space.str_w(w_res) == "a/"
        w_res = space.execute("return File.join('')")
        assert space.str_w(w_res) == ""
        w_res = space.execute("return File.join([])")
        assert space.str_w(w_res) == ""

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
        assert space.str_w(space.execute("return File.basename('ab.rb', '.rb')")) == "ab"
        assert space.str_w(space.execute("return File.basename('ab.rb', 'b.rb')")) == "a"

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

    def test_size_p(self, space, tmpdir):
        w_res = space.execute("return File.size?('%s')" % tmpdir.join("x.txt"))
        assert w_res is space.w_nil
        tmpdir.join("x.txt").ensure()
        w_res = space.execute("return File.size?('%s')" % tmpdir.join("x.txt"))
        assert w_res is space.w_nil
        tmpdir.join("x.txt").write("abc")
        w_res = space.execute("return File.size?('%s')" % tmpdir.join("x.txt"))
        assert space.int_w(w_res) == 3

    def test_delete(self, space, tmpdir):
        tmpdir.join("t.txt").ensure()
        w_res = space.execute("return File.delete('%s')" % tmpdir.join("t.txt"))
        assert space.int_w(w_res) == 1
        assert not tmpdir.join("t.txt").check()


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

    def test_expand_backslash_handling(self, space):
        w_res = space.execute("""
        return File.expand_path("a\\\\b")
        """)
        res = self.unwrap(space, w_res)
        if IS_WINDOWS:
            assert res == "/".join([os.getcwd().replace("\\", "/"), "a", "b"])
        else:
            assert res == os.path.join(os.getcwd(), "a\\b")

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
          File.dirname("/foo/foo"),
          File.dirname("/foo/foo//")
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
            "/foo",
        ]

    def test_windows_backslash_handling(self, space):
        w_res = space.execute("""
        return [
          File.dirname("a/b/c"),
          File.dirname("a\\\\b\\\\//\\\\c/\\\\"),
          File.dirname("\\\\"),
        ]
        """)
        res = self.unwrap(space, w_res)
        if IS_WINDOWS:
            assert res == ["a/b", "a\\b", "/"]
        else:
            assert res == ["a/b", "a\\b\\//\\c", "."]
