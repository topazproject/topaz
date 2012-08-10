import os
import platform

import py

from rupypy.main import entry_point


class TestMain(object):
    def run(self, tmpdir, source=None, status=0, ruby_args=[], argv=[]):
        args = ["rupypy"]
        args += ruby_args
        if source is not None:
            f = tmpdir.join("test.rb")
            f.write(source)
            args.append(str(f))
        else:
            f = None
        args += argv
        res = entry_point(args)
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

    def test_verbose(self, tmpdir, capfd):
        self.run(tmpdir, "puts 5", ruby_args=["-v"])
        out, err = capfd.readouterr()
        [version, out] = out.splitlines()
        assert version.startswith("topaz")
        assert "1.9.3" in version
        assert os.uname()[4] in version
        assert platform.system().lower() in version
        assert out == "5"

        self.run(tmpdir, ruby_args=["-v"])
        out, err = capfd.readouterr()
        [version] = out.splitlines()
        assert version.startswith("topaz")

    def test_arguments(self, tmpdir, capfd):
        self.run(tmpdir, """
        ARGV.each_with_index do |arg, i|
            puts i.to_s + ": " + arg
        end
        """, argv=["abc", "123", "easy"])
        out, err = capfd.readouterr()
        lines = out.splitlines()
        assert lines == [
            "0: abc",
            "1: 123",
            "2: easy",
        ]

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

    def test_traceback_load_const(self, tmpdir, capfd):
        self.assert_traceback(tmpdir, capfd, """
        UnknownConst
        """, [
            "{}:2:in `const_missing': uninitialized constant UnknownConst (NameError)",
            "\tfrom {}:2:in `<main>'",
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

    def test_ruby_engine(self, tmpdir, capfd):
        self.run(tmpdir, "puts RUBY_ENGINE")
        out, err = capfd.readouterr()
        assert out == "topaz\n"

    def test_system_exit(self, tmpdir):
        self.run(tmpdir, "raise SystemExit", 0)
        self.run(tmpdir, "raise SystemExit.new('exit', 1)", 1)
