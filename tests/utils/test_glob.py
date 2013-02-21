import pytest

from ..base import BaseTopazTest
from topaz.utils.glob import Glob
from topaz.objects.regexpobject import RegexpCache
from topaz.objects.fileobject import FNM_NOESCAPE, FNM_DOTMATCH


class GlobHelper(object):
    def __init__(self, space, tmpdir, monkeypatch):
        self.space = space
        self.tmpdir = tmpdir
        self.make_tempdirs(tmpdir)
        monkeypatch.chdir(tmpdir)

    def make_tempdirs(self, tmpdir, mock_files=None):
        if not mock_files:
            mock_files = [
                ".dotfile",
                ".dotsubdir/.dotfile",
                ".dotsubdir/nondotfile",

                "deeply/.dotfile",
                "deeply/nested/.dotfile.ext",
                "deeply/nested/directory/structure/.ext",
                "deeply/nested/directory/structure/bar",
                "deeply/nested/directory/structure/baz",
                "deeply/nested/directory/structure/file_one",
                "deeply/nested/directory/structure/file_one.ext",
                "deeply/nested/directory/structure/foo",
                "deeply/nondotfile",

                "file_one.ext",
                "file_two.ext",

                "dir_filename_ordering",
                "dir/filename_ordering",

                "nondotfile",

                "subdir_one/.dotfile",
                "subdir_one/nondotfile",
                "subdir_two/nondotfile",
                "subdir_two/nondotfile.ext",

                "brace/a",
                "brace/a.js",
                "brace/a.erb",
                "brace/a.js.rjs",
                "brace/a.html.erb",

                "special/+",

                "special/^",
                "special/$",

                "special/(",
                "special/)",
                "special/[",
                "special/]",
                "special/{",
                "special/}",

                "special/test{1}/file[1]",
                ]
            # TODO: Skip these on Windows
            mock_files.extend([
                "special/*",
                "special/?",
                "special/|",
                ])

        for path in mock_files:
            tmpdir.join(path).ensure()

    def glob(self, pattern, flags=0):
        glob = Glob(self.space.fromcache(RegexpCache))
        glob.glob(pattern, flags)
        return glob.matches()

    def sglob(self, pattern, flags=0):
        return sorted(self.glob(pattern, flags))


def pytest_funcarg__glob_helper(request):
    space = request.getfuncargvalue('space')
    tmpdir = request.getfuncargvalue('tmpdir')
    monkeypatch = request.getfuncargvalue('monkeypatch')
    return GlobHelper(space, tmpdir, monkeypatch)


class TestGlob(BaseTopazTest):
    """
    These tests are almost entirely copied from rubyspec. They are included
    separately here because globs are required for running specs.
    """

    def test_absolute(self, glob_helper):
        assert glob_helper.sglob("/") == ["/"]

    def test_non_dotfiles_with_star(self, glob_helper):
        all_files = [
            "brace", "deeply", "dir", "dir_filename_ordering", "file_one.ext",
            "file_two.ext", "nondotfile", "special", "subdir_one",
            "subdir_two"]
        assert glob_helper.sglob("*") == all_files
        assert glob_helper.sglob("**") == all_files
        assert glob_helper.sglob("*file") == ["nondotfile"]

    def test_dotfiles_with_star(self, glob_helper):
        all_files = [".", "..", ".dotfile", ".dotsubdir"]
        assert glob_helper.sglob(".*") == all_files
        assert glob_helper.sglob(".**") == all_files
        assert glob_helper.sglob(".*file") == [".dotfile"]

    def test_empty_pattern_no_matches(self, glob_helper):
        assert glob_helper.glob("") == []

    def test_regexp_specials(self, glob_helper):
        assert glob_helper.glob("special/+") == ["special/+"]
        assert glob_helper.glob("special/^") == ["special/^"]
        assert glob_helper.glob("special/$") == ["special/$"]
        assert glob_helper.glob("special/(") == ["special/("]
        assert glob_helper.glob("special/)") == ["special/)"]
        assert glob_helper.glob("special/\\[") == ["special/["]
        assert glob_helper.glob("special/]") == ["special/]"]
        assert glob_helper.glob("special/\\{") == ["special/{"]
        assert glob_helper.glob("special/\\}") == ["special/}"]

        # TODO: Skip these on Windows
        assert glob_helper.glob("special/\\*") == ["special/*"]
        assert glob_helper.glob("special/\\?") == ["special/?"]
        assert glob_helper.glob("special/|") == ["special/|"]

    def test_matches_paths_with_globs(self, glob_helper):
        assert glob_helper.glob("special/test\\{1\\}/*") == [
            "special/test{1}/file[1]"]

    def test_dstar_recursion(self, glob_helper):
        assert glob_helper.sglob("**/") == [
            "brace/", "deeply/", "deeply/nested/", "deeply/nested/directory/",
            "deeply/nested/directory/structure/", "dir/", "special/",
            "special/test{1}/", "subdir_one/", "subdir_two/"]
        assert glob_helper.sglob("**/*fil*") == [
            "deeply/nested/directory/structure/file_one",
            "deeply/nested/directory/structure/file_one.ext",
            "deeply/nondotfile", "dir/filename_ordering",
            "dir_filename_ordering", "file_one.ext", "file_two.ext",
            "nondotfile", "special/test{1}/file[1]", "subdir_one/nondotfile",
            "subdir_two/nondotfile", "subdir_two/nondotfile.ext"]

    def test_question_mark(self, glob_helper):
        assert glob_helper.sglob("?ubdir_one") == ["subdir_one"]
        assert glob_helper.sglob("subdir_???") == ["subdir_one", "subdir_two"]

    def test_character_group(self, glob_helper):
        assert glob_helper.sglob("[stfu]ubdir_one") == ["subdir_one"]
        assert glob_helper.sglob("[A-Za-z]ubdir_one") == ["subdir_one"]
        assert glob_helper.sglob("subdir_[a-z][a-z][a-z]") == [
            "subdir_one", "subdir_two"]

    def test_negated_character_group(self, glob_helper):
        assert glob_helper.sglob("[^stfu]ubdir_one") == []
        assert glob_helper.sglob("[^wtf]ubdir_one") == ["subdir_one"]
        assert glob_helper.sglob("[^a-zA-Z]ubdir_one") == []
        assert glob_helper.sglob("[^0-9a-fA-F]ubdir_one") == ["subdir_one"]

    def test_braces(self, glob_helper):
        assert glob_helper.sglob("subdir_{one,two,three}") == [
            "subdir_one", "subdir_two"]
        assert glob_helper.sglob("sub*_{one,two,three}") == [
            "subdir_one", "subdir_two"]
        assert glob_helper.sglob("subdir_two/nondotfile{.ext,}") == [
            "subdir_two/nondotfile", "subdir_two/nondotfile.ext"]
        assert glob_helper.sglob("{,.}d*") == [
            ".dotfile", ".dotsubdir", "deeply", "dir", "dir_filename_ordering"]

    def test_braces_ordering(self, glob_helper):
        assert glob_helper.glob("brace/a{.js,.html}{.erb,.rjs}") == [
            "brace/a.js.rjs", "brace/a.html.erb"]
        assert glob_helper.glob("brace/a{.{js,html},}{.{erb,rjs},}") == [
            "brace/a.js.rjs", "brace/a.js", "brace/a.html.erb", "brace/a.erb",
            "brace/a"]

    def test_escaping(self, glob_helper):
        glob_helper.tmpdir.mkdir("foo^bar")
        assert glob_helper.glob("foo?bar") == ["foo^bar"]
        assert glob_helper.glob("foo\\?bar") == []
        assert glob_helper.glob("nond\\otfile") == ["nondotfile"]

    def test_preserves_separator(self, glob_helper):
        assert glob_helper.glob("deeply/nested//directory/*/*.ext") == [
            "deeply/nested//directory/structure/file_one.ext"]
        assert glob_helper.glob("deeply/*/directory/structure//**/*.ext") == [
            "deeply/nested/directory/structure//file_one.ext"]

    def test_ignores_missing_dirs(self, glob_helper):
        assert glob_helper.glob("deeply/notthere/blah*/whatever") == []
        assert glob_helper.glob("deeply/notthere/blah/") == []

    def test_multiple_recursives(self, glob_helper):
        glob_helper.tmpdir.join("a/x/b/y/e").ensure()
        glob_helper.tmpdir.join("a/x/b/y/b/z/e").ensure()
        print glob_helper.sglob("a/**/b/**/e")
        assert glob_helper.sglob("a/**/b/**/e") == [
            "a/x/b/y/b/z/e", "a/x/b/y/e"]

    def test_flag_dotmatch(self, glob_helper):
        all_files = [
            ".", "..", ".dotfile", ".dotsubdir", "brace", "deeply", "dir",
            "dir_filename_ordering", "file_one.ext", "file_two.ext",
            "nondotfile", "special", "subdir_one", "subdir_two"]
        assert glob_helper.sglob("*", FNM_DOTMATCH) == all_files
        assert glob_helper.sglob("**", FNM_DOTMATCH) == all_files
        assert glob_helper.sglob("*file", FNM_DOTMATCH) == [
            ".dotfile", "nondotfile"]
        assert glob_helper.sglob("**/", FNM_DOTMATCH) == [
            ".dotsubdir/", "brace/", "deeply/", "deeply/nested/",
            "deeply/nested/directory/", "deeply/nested/directory/structure/",
            "dir/", "special/", "special/test{1}/", "subdir_one/",
            "subdir_two/"]
        assert glob_helper.sglob("./**/", FNM_DOTMATCH) == [
            "./", "./.dotsubdir/", "./brace/", "./deeply/", "./deeply/nested/",
            "./deeply/nested/directory/",
            "./deeply/nested/directory/structure/", "./dir/", "./special/",
            "./special/test{1}/", "./subdir_one/", "./subdir_two/"]

    def test_flag_noescape(self, glob_helper):
        # TODO: Skip this on Windows
        glob_helper.tmpdir.mkdir("foo?bar")
        assert glob_helper.glob("foo?bar", FNM_NOESCAPE) == ["foo?bar"]
        assert glob_helper.glob("foo\\?bar", FNM_NOESCAPE) == []
        glob_helper.tmpdir.mkdir("foo\\?bar")
        assert glob_helper.glob("foo\\?bar", FNM_NOESCAPE) == ["foo\\?bar"]
