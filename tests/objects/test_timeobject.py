import time

from rupypy.objects.timeobject import W_TimeObject

from ..base import BaseRuPyPyTest


class TestTimeObject(BaseRuPyPyTest):
    def mock_time(self, monkeypatch, value=1000.0):
        def mocktime():
            return value
        monkeypatch.setattr(time, 'time', mocktime)

    def test_now(self, space, monkeypatch):
        self.mock_time(monkeypatch)
        w_res = space.execute("return Time.now")
        assert isinstance(w_res, W_TimeObject)
        assert w_res.epoch == 1000.0

    def test_to_s(self, space, monkeypatch):
        self.mock_time(monkeypatch)
        w_res = space.execute("return Time.now.to_s")
        assert space.str_w(w_res) == time.strftime("%Y-%m-%d %H:%M:%S %z", time.localtime(1000.0))

    def test_to_f(self, space, monkeypatch):
        self.mock_time(monkeypatch)
        w_res = space.execute("return Time.now.to_f")
        assert space.float_w(w_res) == 1000.0

    def test_minus(self, space, monkeypatch):
        self.mock_time(monkeypatch)
        w_time1 = space.execute("return Time.now")
        self.mock_time(monkeypatch, 750.0)
        w_time2 = space.execute("return Time.now")
        w_time3 = space.send(w_time1, space.newsymbol("-"), [w_time2])
        assert w_time3.epoch == 250.0

    def test_at(self, space, monkeypatch):
        w_res = space.execute("return Time.at(0)")
        assert w_res.epoch == 0.0
        w_res = space.execute("return Time.at(0, 5)")
        assert w_res.epoch == 0.005
        w_res = space.execute("return Time.at(0, 5)")
        assert w_res.epoch == 0.005
        self.mock_time(monkeypatch)
        w_res = space.execute("""
        t1 = Time.now
        t2 = Time.at(t1)
        return t1, t2
        """)
        t1, t2 = space.listview(w_res)
        assert t1 is not t2
        assert t1.epoch == t2.epoch
