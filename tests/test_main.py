from rupypy.main import entry_point


class TestMain(object):
    def run(self, tmpdir, source):
        f = tmpdir.join("test.rb")
        f.write(source)
        res = entry_point(["rupypy", str(f)])
        assert not res
        return f

    def test_simple(self, tmpdir, capfd):
        self.run(tmpdir, "puts 5")
        out, err = capfd.readouterr()
        assert out == "5\n"
        assert not err

    def test___FILE__(self, tmpdir, capfd):
        f = self.run(tmpdir, "puts __FILE__")
        out, err = capfd.readouterr()
        assert out == "{}\n".format(f)
