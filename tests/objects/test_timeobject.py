import os

from topaz.objects.timeobject import W_TimeObject
from topaz.utils import time

UTC_ENV = os.environ.copy()
UTC_ENV["TZ"] = "UTC+0"


class TestTimeObject(object):
    def epoch(self, space, tz='UTC+0'):
        try:
            orig_tz = os.environ.get('TZ')
            os.environ['TZ'] = tz
            time.tzset(space)
            return time.localtime(space, space.newfloat(0.0))
        finally:
            if orig_tz is not None:
                os.environ['TZ'] = orig_tz
            time.tzset(space)

    def test_now(self, space, monkeypatch):
        monkeypatch.setattr(os, "environ", UTC_ENV)
        monkeypatch.setattr(time, "time", lambda: 123.4)
        w_secs = space.execute("return Time.now.to_f")
        assert space.float_w(w_secs) == 123.4

    def test_subtraction(self, space, monkeypatch):
        monkeypatch.setattr(W_TimeObject, "get_time_struct", self.epoch)
        w_secs = space.execute("""
        return Time.mktime(1970, 1, 1, 1) - Time.mktime(1970, 1, 1, 0)
        """)
        assert space.float_w(w_secs) == 3600.0

    def test_to_s(self, space, monkeypatch):
        monkeypatch.setattr(W_TimeObject, "get_time_struct", self.epoch)
        monkeypatch.setattr(os, "environ", UTC_ENV)
        w_str = space.execute("return Time.mktime(1970, 1, 1).to_s")
        # FIXME figure out timezone stuff so that this is a stronger assertion
        assert space.str_w(w_str).startswith("1970-01-01 00:00:00")
