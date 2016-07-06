import os

from ..base import BaseTopazTest


class TestDir(BaseTopazTest):
    def test_name(self, space):
        space.execute("Dir")

    def test_pwd(self, space):
        w_res = space.execute("return Dir.pwd")
        assert space.str_w(w_res) == os.getcwd()
        w_res = space.execute("return Dir.getwd")
        assert space.str_w(w_res) == os.getcwd()

    def test_read(self, space, tmpdir):
        d = tmpdir.mkdir("sub_test_read")
        f = d.join("content")
        f.write("hello")
        f = d.join("content2")
        f.write("hello")
        w_res = space.execute("""
        d = Dir.new('%s')
        return [d.read, d.read, d.read, d.read, d.read]
        """ % d)
        res = self.unwrap(space, w_res)
        res.sort()
        assert res == [None, ".", "..", "content", "content2"]

    def test_new(self, space, tmpdir):
        d = tmpdir.mkdir("sub")
        f = d.join("content")
        f.write("hello")
        space.execute("Dir.new('%s')" % d)
        with self.raises(space, "Errno::ENOENT"):
            space.execute("Dir.new('this does not exist')")
        with self.raises(space, "Errno::ENOTDIR"):
            space.execute("Dir.new('%s')" % f)

    def test_delete(self, space, tmpdir):
        d = tmpdir.mkdir("sub")
        space.execute("Dir.delete('%s')" % d)
        assert not tmpdir.listdir()
        d = tmpdir.mkdir("sub")
        f = d.join("content")
        f.write("hello")
        with self.raises(space, "Errno::ENOTEMPTY"):
            space.execute("Dir.delete('%s')" % d)

    def test_mkdir(self, space, tmpdir):
        space.execute("Dir.mkdir(File.join('%s', 'madedir'))" % tmpdir)
        assert tmpdir.join("madedir").check()
        assert tmpdir.join("madedir").stat().mode & 0100 == 0100

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

    def test_glob(self, space, tmpdir):
        sub1 = tmpdir.mkdir("sub1")
        sub2 = tmpdir.mkdir("sub2")
        sub1.join("sub1content1").ensure()
        sub1.join("sub1content2").ensure()
        sub2.join("sub2content1").ensure()
        sub2.join("sub2content2").ensure()
        w_res = space.execute("""
        Dir.chdir('%s') do
          return Dir['*']
        end
        """ % tmpdir)
        res = self.unwrap(space, w_res)
        res.sort()
        assert res == ["sub1", "sub2"]
        w_res = space.execute("""
        Dir.chdir('%s') do
          return Dir['**/*']
        end
        """ % tmpdir)
        res = self.unwrap(space, w_res)
        res.sort()
        assert res == ["sub1", "sub1/sub1content1", "sub1/sub1content2", "sub2", "sub2/sub2content1", "sub2/sub2content2"]
        w_res = space.execute("""
        Dir.chdir('%s') do
          return Dir['**/*{1con}*']
        end
        """ % tmpdir)
        res = self.unwrap(space, w_res)
        res.sort()
        assert res == ["sub1/sub1content1", "sub1/sub1content2"]
        w_res = space.execute("""
        Dir.chdir('%s') do
          return Dir['**/sub[1]content[12]']
        end
        """ % tmpdir)
        res = self.unwrap(space, w_res)
        res.sort()
        assert res == ["sub1/sub1content1", "sub1/sub1content2"]
        w_res = space.execute("""
        Dir.chdir('%s') do
          return Dir['%s/']
        end
        """ % (tmpdir, tmpdir.join("..")))
        assert self.unwrap(space, w_res) == [str(tmpdir.join("..")) + "/"]
        w_res = space.execute("""
        Dir.chdir('%s') do
          return Dir["sub1\\0foo", "sub\\02bar"], Dir["sub1\\0foo"]
        end
        """ % tmpdir)
        res = self.unwrap(space, w_res)
        assert res == [["sub1"], ["sub1"]]

    def test_close(self, space, tmpdir):
        with self.raises(space, "IOError", "closed directory"):
            space.execute("""
            d = Dir.new('%s')
            d.close
            d.close
            """ % tmpdir)
        with self.raises(space, "IOError", "closed directory"):
            space.execute("""
            d = Dir.new('%s')
            d.close
            d.read
            """ % tmpdir)
