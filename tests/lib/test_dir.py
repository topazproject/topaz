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
            
    def test_glob(self, space):
        w_res = space.execute("return Dir.glob('AUTH*.*')")
        assert ['AUTHORS.rst'] == space.listview(w_res)
        w_res = space.execute("return Dir.glob(['A*', 'ru*'])")
        assert ['rupypy', 'AUTHORS.rst'] == space.listview(w_res)
        w_res = space.execute("return Dir.glob(['*pypy', 'ru*'])")
        assert ['rupypy'] == space.listview(w_res)