import py

from rupypy.main import entry_point


class TestMain(object):
    def run(self, tmpdir, source, status=0):
        f = tmpdir.join("test.rb")
        f.write(source)
        res = entry_point(["rupypy", str(f)])
        assert res == status
        return f

    def assert_traceback(self, tmpdir, capfd, src, expected):
        f = self.run(tmpdir, src, status=1)
        out, err = capfd.readouterr()
        assert not out
        actual_lines = err.splitlines()
        expected_lines = []
        for line in expected:
            expected_lines.append(line.format(f))
        assert actual_lines == expected_lines

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
        self.assert_traceback(tmpdir, capfd, """
        def f
            yield
        end

        f { 1 / 0}
        """, [
            "{}:6:in `/': divided by 0 (ZeroDivisionError)",
            "\tfrom {}:6:in `block in <main>'",
            "\tfrom {}:3:in `f'",
            "\tfrom {}:6:in `<main>'",
        ])

    @py.test.mark.xfail
    def test_traceback_default_arg(self, tmpdir, capfd):
        self.assert_traceback(tmpdir, capfd, """
        def f(a=1/2)
        end
        f
        """, [
            "{}:2:in `/': divided by 0 (ZeroDivisionError)",
            "\tfrom {}:2:in `f'",
            "\tfrom {}:4:in `<main>'",
        ])
