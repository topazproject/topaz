import os

from ..base import BaseRuPyPyTest


class TestDir(BaseRuPyPyTest):
    def test_name(self, space):
        space.execute("Dir")

    def test_pwd(self, space):
        w_res = space.execute("return Dir.pwd")
        assert space.str_w(w_res) == os.getcwd()

    def test_new(self, space, tmpdir):
        d = tmpdir.mkdir("sub")
        f = d.join("content")
        f.write("hello")
        space.execute("Dir.new('%s')" % str(d))
        with self.raises(space, "SystemCallError"):
            space.execute("Dir.new('this does not exist')")
        with self.raises(space, "SystemCallError"):
            space.execute("Dir.new('%s')" % str(f))

    def test_delete(self, space, tmpdir):
        d = tmpdir.mkdir("sub")
        space.execute("Dir.delete('%s')" % str(d))
        assert not tmpdir.listdir()
        d = tmpdir.mkdir("sub")
        f = d.join("content")
        f.write("hello")
        with self.raises(space, "SystemCallError"):
            space.execute("Dir.delete('%s')" % str(d))

    def test_existp(self, space, tmpdir):
        d = tmpdir.mkdir("sub")
        assert space.execute("return Dir.exist?('%s')" % str(d)) is space.w_true
        assert space.execute("return Dir.exists?('%s')" % str(d)) is space.w_true

    def test_home(self, space):
        w_res = space.execute("return Dir.home")
        assert space.str_w(w_res) == os.path.expanduser("~")

    def test_open(self, space, tmpdir):
        d = tmpdir.mkdir("sub")
        f = d.join("content")
        f.write("hello")
        space.execute("Dir.open('%s')" % str(d))
        with self.raises(space, "SystemCallError"):
            space.execute("Dir.open('this does not exist')")
        w_res = space.execute("return Dir.open('%s') {|d| d.path } " % str(d))
        assert space.str_w(w_res) == str(d)

    def test_open(self, space, tmpdir):
        d = tmpdir.mkdir("sub")
        f = d.join("content")
        f.write("hello")
        f = d.join("content2")
        f.write("hello")
        w_res = space.execute("Dir.entries('%s')" % str(d))
        assert self.unwrap(space, w_res) == ["content", "content2"]
