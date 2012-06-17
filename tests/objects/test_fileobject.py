import os

from ..base import BaseRuPyPyTest


class TestExpandPath(BaseRuPyPyTest):
    def test_expand_to_absolute(self, space):
        w_res = space.execute("""
        return [File.expand_path(""), File.expand_path("a"), File.expand_path("a", nil)]
        """)
        assert self.unwrap(space, w_res) == [
            os.getcwd(),
            os.path.join(os.getcwd(), "a"),
            os.path.join(os.getcwd(), "a"),
        ]

    def test_covert_to_absolute_using_provided_base(self, space):
        w_res = space.execute("""return File.expand_path("", "/tmp")""")
        assert self.unwrap(space, w_res) == "/tmp"
        w_res = space.execute("""return File.expand_path("a", "/tmp")""")
        assert self.unwrap(space, w_res) == "/tmp/a"
        w_res = space.execute("""return File.expand_path("../a", "/tmp/xxx")""")
        assert self.unwrap(space, w_res) == "/tmp/a"
        w_res = space.execute("""return File.expand_path(".", "/")""")
        assert self.unwrap(space, w_res) == "/"

    def test_home_expansion(self, space):
        w_res = space.execute("""return File.expand_path("~")""")
        assert self.unwrap(space, w_res) == os.environ["HOME"]
        w_res = space.execute("""return File.expand_path("~", "/tmp/random")""")
        assert self.unwrap(space, w_res) == os.environ["HOME"]
        w_res = space.execute("""return File.expand_path("~/a", "/tmp/random")""")
        assert self.unwrap(space, w_res) == os.path.join(os.environ["HOME"], "a")


class TestDirname(BaseRuPyPyTest):
    def test_simple(self, space):
        w_res = space.execute("""
        return [
            File.dirname("/home/guido"),
            File.dirname("/home/guido/test.txt"),
            File.dirname("test.txt"),
            File.dirname("/home///guido//file.txt"),
            File.dirname(""),
            File.dirname("/"),
            File.dirname("/foo/foo")
        ]
        """)
        assert self.unwrap(space, w_res) == [
            "/home",
            "/home/guido",
            ".",
            "/home///guido",
            ".",
            "/",
            "/foo",
        ]
