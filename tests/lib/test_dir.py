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
        space.execute("Dir.new('%s')" % d)
        with self.raises(space, "SystemCallError"):
            space.execute("Dir.new('this does not exist')")
        with self.raises(space, "SystemCallError"):
            space.execute("Dir.new('%s')" % f)

    def test_delete(self, space, tmpdir):
        d = tmpdir.mkdir("sub")
        space.execute("Dir.delete('%s')" % d)
        assert not tmpdir.listdir()
        d = tmpdir.mkdir("sub")
        f = d.join("content")
        f.write("hello")
        with self.raises(space, "SystemCallError"):
            space.execute("Dir.delete('%s')" % d)

    def test_chdir(self, space, tmpdir, monkeypatch):
        w_res = space.execute("""
        dirs = []
        dirs << Dir.pwd
        Dir.chdir('%s') do
            dirs << Dir.pwd
        end
        dirs << Dir.pwd
        return dirs
        """ % tmpdir)
        paths = [os.getcwd(), os.path.realpath(str(tmpdir)), os.getcwd()]
        assert self.unwrap(space, w_res) == paths

        monkeypatch.setenv("HOME", str(tmpdir))
        w_res = space.execute("""
        Dir.chdir do
            return Dir.pwd
        end
        """)

        assert space.str_w(w_res) == os.path.realpath(str(tmpdir))
