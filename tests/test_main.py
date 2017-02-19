import os
import platform
import subprocess

from topaz.main import _entry_point


class TestMain(object):
    def run(self, space, tmpdir, source=None, status=0, ruby_args=[], argv=[]):
        args = ["topaz"]
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
        self.run(space, tmpdir, None, ruby_args=["-e", "puts 5", "-e", "puts 6"])
        out, err = capfd.readouterr()
        assert out == "5\n6\n"
        self.run(space, tmpdir, None, ruby_args=["-eputs 'hi'"])
        out, err = capfd.readouterr()
        assert out == "hi\n"

    def test_no_expr(self, space, tmpdir, capfd):
        self.run(space, tmpdir, None, ruby_args=["-e"], status=1)
        out, err = capfd.readouterr()
        assert err == u"no code specified for -e (RuntimeError)\n"
        assert out == ""

    def test___FILE__(self, space, tmpdir, capfd):
        f = self.run(space, tmpdir, "puts __FILE__")
        out, err = capfd.readouterr()
        assert out == "{}\n".format(f)

    def test_verbose(self, space, tmpdir, capfd):
        self.run(space, tmpdir, "puts 5", ruby_args=["-v"])
        out, err = capfd.readouterr()
        [version, out] = out.splitlines()
        assert version.startswith("topaz")
        assert "2.4.0" in version
        assert os.uname()[4] in version
        assert platform.system().lower() in version
        assert subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).rstrip() in version
        assert out == "5"

        self.run(space, tmpdir, ruby_args=["-v"])
        out, err = capfd.readouterr()
        [version] = out.splitlines()
        assert version.startswith("topaz")

    def test_debug_defaults_to_false(self, space, tmpdir, capfd):
        self.run(space, tmpdir, "puts $DEBUG")
        out, _ = capfd.readouterr()
        assert out.strip() == "false"

    def test_debug_sets_verbose(self, space, tmpdir, capfd):
        self.run(space, tmpdir, "puts $VERBOSE", ruby_args=["-d"])
        out, _ = capfd.readouterr()
        assert out.strip() == "true"

    def test_debug_sets_dash_d(self, space, tmpdir, capfd):
        self.run(space, tmpdir, "puts $-d", ruby_args=["-d"])
        out, _ = capfd.readouterr()
        assert out.strip() == "true"

    def test_dash_w_defaults_to_false(self, space, tmpdir, capfd):
        self.run(space, tmpdir, "puts $-w")
        out, _ = capfd.readouterr()
        assert out.strip() == "false"

    def test_warnings_sets_dash_w(self, space, tmpdir, capfd):
        self.run(space, tmpdir, "puts $-w", ruby_args=["-w"])
        out, _ = capfd.readouterr()
        assert out.strip() == "true"

    def test_warning_level_defaults_to_verbose_true(self, space, tmpdir, capfd):
        self.run(space, tmpdir, "puts $VERBOSE", ruby_args=["-W"])
        out, _ = capfd.readouterr()
        assert out.strip() == "true"

    def test_help(self, space, tmpdir, capfd):
        self.run(space, tmpdir, ruby_args=["-h"])
        out, _ = capfd.readouterr()
        assert out.splitlines()[0] == "Usage: topaz [switches] [--] [programfile] [arguments]"

    def test_copyright(self, space, tmpdir, capfd):
        self.run(space, tmpdir, ruby_args=["--copyright"])
        out, _ = capfd.readouterr()
        [copyright] = out.splitlines()
        assert copyright.startswith("topaz")
        assert "Alex Gaynor" in copyright

    def test_version(self, space, tmpdir, capfd):
        self.run(space, tmpdir, ruby_args=["--version"])
        out, _ = capfd.readouterr()
        [version] = out.splitlines()
        assert version.startswith("topaz")
        assert "2.4.0" in version
        assert os.uname()[4] in version
        assert platform.system().lower() in version
        assert subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).rstrip() in version

    def test_stop_consuming_args(self, space, tmpdir, capfd):
        self.run(space, tmpdir, ruby_args=["-e", "puts ARGV.join(' ')", "--", "--help", "-e"])
        out, _ = capfd.readouterr()
        assert out == "--help -e\n"

    def test_load_path_multiple_args(self, space, tmpdir, capfd):
        d = tmpdir.mkdir("sub")
        f1 = d.join("f.rb")
        f1.write("""
        Const = 5
        """)
        self.run(space, tmpdir, """
        require "f"
        puts Const
        """, ruby_args=["-I", str(d)])
        out, _ = capfd.readouterr()
        assert out == "5\n"

    def test_load_path_joined_args(self, space, tmpdir, capfd):
        d = tmpdir.mkdir("sub")
        f1 = d.join("f.rb")
        f1.write("""
        Const = 10
        """)
        self.run(space, tmpdir, """
        require "f"
        puts Const
        """, ruby_args=["-I%s" % d])
        out, _ = capfd.readouterr()
        assert out == "10\n"

    def test_load_path_path_separated(self, space, tmpdir, capfd):
        d1 = tmpdir.mkdir("sub")
        d2 = tmpdir.mkdir("sub2")
        f1 = d1.join("f1.rb")
        f1.write("""
        Const1 = 20
        """)
        f2 = d2.join("f2.rb")
        f2.write("""
        require "f1"
        Const2 = 3
        """)
        self.run(space, tmpdir, """
        require "f2"
        puts Const1 + Const2
        """, ruby_args=["-I%s:%s" % (d1, d2)])
        out, _ = capfd.readouterr()
        assert out == "23\n"

    def test_require_multiple_args(self, space, tmpdir, capfd):
        d = tmpdir.mkdir("sub")
        f = d.join("zyx.rb")
        f.write("""
        Zyx = 9
        """)
        self.run(space, tmpdir, "puts Zyx", ruby_args=["-r", "zyx", "-I", str(d)])
        out, _ = capfd.readouterr()
        assert out == "9\n"

    def test_require_joined_args(self, space, tmpdir, capfd):
        d = tmpdir.mkdir("sub")
        f = d.join("zyx.rb")
        f.write("""
        Zyx = 7
        """)
        self.run(space, tmpdir, "puts Zyx", ruby_args=["-rzyx", "-I", str(d)])
        out, _ = capfd.readouterr()
        assert out == "7\n"

    def test_search_path(self, space, tmpdir, capfd, monkeypatch):
        f = tmpdir.join("a")
        f.write("puts 17")
        monkeypatch.setenv("PATH", "%s:%s" % (tmpdir, os.environ["PATH"]))
        self.run(space, tmpdir, ruby_args=["-S", "a"])
        out, _ = capfd.readouterr()
        assert out == "17\n"

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
            "{}: line 2 (unexpected Token(DO_COND, do)) (SyntaxError)",
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
        puts "#{RUBY_ENGINE} (ruby-#{RUBY_VERSION}p#{RUBY_PATCHLEVEL}) (git rev #{RUBY_REVISION}) [#{RUBY_PLATFORM}]"
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

    def test_program_global(self, space, tmpdir, capfd):
        self.run(space, tmpdir, None, ruby_args=["-e", "puts $0"])
        out1, err1 = capfd.readouterr()
        assert out1 == "-e\n"
        f = self.run(space, tmpdir, "puts $0")
        out2, err2 = capfd.readouterr()
        assert out2 == "{}\n".format(f)
        f = self.run(space, tmpdir, "puts $PROGRAM_NAME")
        out3, _ = capfd.readouterr()
        assert out3 == "{}\n".format(f)

    def test_non_existent_file(self, space, tmpdir, capfd):
        self.run(space, tmpdir, None, ruby_args=[str(tmpdir.join("t.rb"))], status=1)
        out, err = capfd.readouterr()
        assert err == "No such file or directory -- %s (LoadError)\n" % tmpdir.join("t.rb")
