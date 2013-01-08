import os

from ..base import BaseTopazTest


class TestEnvObject(BaseTopazTest):
    def test_get(self, space, monkeypatch):
        monkeypatch.setenv("ABC", "12")
        w_res = space.execute("return ENV['ABC']")
        assert self.unwrap(space, w_res) == "12"

    def test_get_nonexistant(self, space, monkeypatch):
        monkeypatch.delenv("ZZZZ", raising=False)
        w_res = space.execute("return ENV['ZZZZ']")
        assert self.unwrap(space, w_res) is None

    def test_set(self, space, monkeypatch):
        monkeypatch.delenv("ZZZZ", raising=False)
        w_res = space.execute("""
        ENV['ZZZZ'] = "/home/newhome"
        return ENV['ZZZZ']
        """)
        assert space.str_w(w_res) == os.environ["ZZZZ"] == "/home/newhome"

    def test_class(self, space):
        w_res = space.execute("return ENV.class")
        assert w_res is space.w_object
