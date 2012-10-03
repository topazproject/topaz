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
