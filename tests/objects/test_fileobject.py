import os

from ..base import BaseRuPyPyTest


class TestExpandPath(BaseRuPyPyTest):
    def test_expand_to_absolute(self, ec):
        w_res = ec.space.execute(ec, """
        return [File.expand_path(""), File.expand_path("a"), File.expand_path("a", nil)]
        """)
        assert self.unwrap(ec.space, w_res) == [
            os.getcwd(),
            os.path.join(os.getcwd(), "a"),
            os.path.join(os.getcwd(), "a"),
        ]

    def test_covert_to_absolute_using_provided_base(self, ec):
        w_res = ec.space.execute(ec, """return File.expand_path("", "/tmp")""")
        assert self.unwrap(ec.space, w_res) == "/tmp"
        w_res = ec.space.execute(ec, """return File.expand_path("a", "/tmp")""")
        assert self.unwrap(ec.space, w_res) == "/tmp/a"
        w_res = ec.space.execute(ec, """return File.expand_path("../a", "/tmp/xxx")""")
        assert self.unwrap(ec.space, w_res) == "/tmp/a"
        w_res = ec.space.execute(ec, """return File.expand_path(".", "/")""")
        assert self.unwrap(ec.space, w_res) == "/"

    def test_home_expansion(self, ec):
        w_res = ec.space.execute(ec, """return File.expand_path("~")""")
        assert self.unwrap(ec.space, w_res) == os.environ["HOME"]
        w_res = ec.space.execute(ec, """return File.expand_path("~", "/tmp/random")""")
        assert self.unwrap(ec.space, w_res) == os.environ["HOME"]
        w_res = ec.space.execute(ec, """return File.expand_path("~/a", "/tmp/random")""")
        assert self.unwrap(ec.space, w_res) == os.path.join(os.environ["HOME"], "a")
