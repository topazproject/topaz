from rupypy.main import entry_point


class TestMain(object):
    def run(self, tmpdir, source, status=0):
        f = tmpdir.join("test.rb")
        f.write(source)
        res = entry_point(["rupypy", str(f)])
        assert res == status
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

    def test_traceback_printed(self, tmpdir, capfd):
        f = self.run(tmpdir, """
        def f
            yield
        end

        f { 1 / 0}
        """, status=1)
        out, err = capfd.readouterr()
        assert not out
        lines = err.splitlines()
        assert lines == [
            "{}:6:in `/': divided by 0 (ZeroDivisionError)".format(f),
            "\tfrom {}:6:in `block in <main>'".format(f),
            "\tfrom {}:3:in `f'".format(f),
            "\tfrom {}:6:in `<main>'".format(f),
        ]
