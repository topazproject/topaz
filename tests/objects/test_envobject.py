from ..base import BaseRuPyPyTest


class TestEnvObject(BaseRuPyPyTest):
    def test_get(self, space, monkeypatch):
        monkeypatch.setenv("ABC", "12")
        w_res = space.execute("return ENV['ABC']")
        assert self.unwrap(space, w_res) == "12"
