import os
import platform

import pytest

from rupypy.main import _entry_point


class TestMain(object):
    def run(self, space, tmpdir, source=None, status=0, ruby_args=[], argv=[]):
        args = ["rupypy"]
        args += ruby_args
        if source is not None:
            f = tmpdir.join("test.rb")
            f.write(source)
            args.append(str(f))
        else:
            f = None
        args += argv
        res = _entry_point(space, args)
        assert res == status
        return f

    def assert_traceback(self, space, tmpdir, capfd, src, expected):
        f = self.run(space, tmpdir, src, status=1)
        out, err = capfd.readouterr()
        assert not out
        actual_lines = err.splitlines()
        expected_lines = []
        for line in expected:
            expected_lines.append(line.format(f))
        assert actual_lines == expected_lines

    def test_simple(self, space, tmpdir, capfd):
        self.run(space, tmpdir, "puts 5")
        out, err = capfd.readouterr()
        assert out == "5\n"
        assert not err

    def test_expr(self, space, tmpdir, capfd):
        self.run(space, tmpdir, None, ruby_args=['-e', 'puts 5', '-e', 'puts 6'])
        out, err = capfd.readouterr()
        assert out == "5\n6\n"

    def test___FILE__(self, space, tmpdir, capfd):
        f = self.run(space, tmpdir, "puts __FILE__")
        out, err = capfd.readouterr()
        assert out == "{}\n".format(f)

    def test_verbose(self, space, tmpdir, capfd):
        self.run(space, tmpdir, "puts 5", ruby_args=["-v"])
        out, err = capfd.readouterr()
        [version, out] = out.splitlines()
        assert version.startswith("topaz")
        assert "1.9.3" in version
        assert os.uname()[4] in version
        assert platform.system().lower() in version
        assert out == "5"

        self.run(space, tmpdir, ruby_args=["-v"])
        out, err = capfd.readouterr()
        [version] = out.splitlines()
        assert version.startswith("topaz")

    def test_arguments(self, space, tmpdir, capfd):
        self.run(space, tmpdir, """
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

    def test_traceback_printed(self, space, tmpdir, capfd):
        self.assert_traceback(space, tmpdir, capfd, """
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

    def test_syntax_error(self, space, tmpdir, capfd):
        self.assert_traceback(space, tmpdir, capfd, """
        while do
        """, [
            "{}: line 2 (SyntaxError)",
        ])

    def test_traceback_load_const(self, space, tmpdir, capfd):
        self.assert_traceback(space, tmpdir, capfd, """
        UnknownConst
        """, [
            "{}:2:in `const_missing': uninitialized constant UnknownConst (NameError)",
            "\tfrom {}:2:in `<main>'",
        ])

    def test_traceback_class(self, space, tmpdir, capfd):
        self.assert_traceback(space, tmpdir, capfd, """
        class X
            1 / 0
        end
        """, [
            "{}:3:in `/': divided by 0 (ZeroDivisionError)",
            "\tfrom {}:3:in `<class:X>'",
            "\tfrom {}:1:in `<main>'",
        ])

    @pytest.mark.xfail
    def test_traceback_default_arg(self, space, tmpdir, capfd):
        self.assert_traceback(space, tmpdir, capfd, """
        def f(a=1 / 0)
        end
        f
        """, [
            "{}:2:in `/': divided by 0 (ZeroDivisionError)",
            "\tfrom {}:2:in `f'",
            "\tfrom {}:4:in `<main>'",
        ])

    def test_ruby_engine(self, space, tmpdir, capfd):
        self.run(space, tmpdir, "puts RUBY_ENGINE")
        out, err = capfd.readouterr()
        assert out == "topaz\n"

    def test_ruby_description(self, space, tmpdir, capfd):
        self.run(space, tmpdir, "puts RUBY_DESCRIPTION")
        out1, err1 = capfd.readouterr()
        self.run(space, tmpdir, """
        puts "#{RUBY_ENGINE} (ruby-#{RUBY_VERSION}p#{RUBY_PATCHLEVEL}) [#{RUBY_PLATFORM}]"
        """)
        out2, err2 = capfd.readouterr()
        assert out1 == out2

    def test_system_exit(self, space, tmpdir):
        self.run(space, tmpdir, "raise SystemExit", 0)
        self.run(space, tmpdir, "raise SystemExit.new('exit', 1)", 1)

    def test_at_exit(self, space, tmpdir, capfd):
        f = self.run(space, tmpdir, """
        at_exit { puts "1" }
        at_exit { 1 / 0 }
        at_exit { puts "2" }
        1 / 0
        """, status=1)
        out, err = capfd.readouterr()
        assert out.splitlines() == [
            "2",
            "1",
        ]
        assert err.splitlines() == [
            "{}:3:in `/': divided by 0 (ZeroDivisionError)".format(f),
            "\tfrom {}:3:in `block in <main>'".format(f),
            "{}:5:in `/': divided by 0 (ZeroDivisionError)".format(f),
            "\tfrom {}:5:in `<main>'".format(f),
        ]
