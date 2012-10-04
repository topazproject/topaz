import os

from ..base import BaseRuPyPyTest


class TestEnvObject(BaseRuPyPyTest):
    def test_get(self, space, monkeypatch):
        monkeypatch.setenv("ABC", "12")
        w_res = space.execute("return ENV['ABC']")
        assert self.unwrap(space, w_res) == "12"

    def test_get_nonexistant(self, space, monkeypatch):
        monkeypatch.delenv("ZZZZ", raising=False)
        w_res = space.execute("return ENV['ZZZZ']")
        assert self.unwrap(space, w_res) is None

    def test_set(self, space, monkeypatch):
        w_res = space.execute("""
        ENV['ZZZZ'] = '/home/newhome'
        return ENV['ZZZZ']
        """)
        assert space.str_w(w_res) == "/home/newhome"
        assert os.environ.get("ZZZZ") == "/home/newhome"
        monkeypatch.delenv("ZZZZ", raising=False)

    def test_set_get_stringish(self, space, monkeypatch):
        w_res = space.execute("""
        class A; def to_str; "ZZZZ"; end; end
        ENV[A.new] = A.new
        return ENV[A.new]
        """)
        assert space.str_w(w_res) == "ZZZZ"
        assert os.environ.get("ZZZZ") == "ZZZZ"
        monkeypatch.delenv("ZZZZ", raising=False)

    def test_class(self, space):
        w_res = space.execute("return ENV.class")
        assert w_res == self.find_const(space, "Object")
