import os

from topaz.objects.timeobject import W_TimeObject
from topaz.utils import time


class TestTimeObject(object):
    def test_now(self, space, monkeypatch):
        monkeypatch.setattr(time, "time", lambda: 342.1)
        monkeypatch.setenv("TZ", "UTC+0")
        w_secs = space.execute("return Time.now.to_f")
        assert space.float_w(w_secs) == 342.1

    def test_subtraction(self, space):
        w_secs = space.execute("""
        return Time.mktime(1970, 1, 1, 1) - Time.mktime(1970, 1, 1, 0)
        """)
        assert space.float_w(w_secs) == 3600.0

    def test_to_s(self, space):
        w_str = space.execute("return Time.mktime(1970, 1, 1).to_s")
        # FIXME figure out timezone stuff wrt strftime so that this is a
        # stronger assertion
        assert space.str_w(w_str).startswith("1970-01-01 00:00:00")
