import os
import time

import pytest

from topaz.objects.timeobject import W_TimeObject

UTC_ENV = os.environ.copy()
UTC_ENV["TZ"] = "UTC+0"


class TestTimeObject(object):
    def epoch(self, tz='UTC+0'):
        try:
            orig_tz = os.environ.get('TZ')
            os.environ['TZ'] = tz
            return time.localtime(0)
        finally:
            if orig_tz is not None:
                os.environ['TZ'] = orig_tz

    def epoch_plus_hour(self, tz='UTC+0'):
        t = self.epoch(tz)
        return time.struct_time((
            t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour + 1,
            t.tm_min, t.tm_sec, t.tm_wday, t.tm_yday, t.tm_isdst
        ))

    def test_now(self, space, monkeypatch):
        monkeypatch.setattr(os, "environ", UTC_ENV)
        monkeypatch.setattr(W_TimeObject, "get_time_struct", self.epoch)
        w_secs = space.execute("return Time.now.to_f")
        assert space.float_w(w_secs) == 0.0

    def test_subtraction(self, space, monkeypatch):
        monkeypatch.setattr(W_TimeObject, "get_time_struct",
            iter([self.epoch_plus_hour(), self.epoch()]).next)
        w_secs = space.execute("return Time.now - Time.now")
        assert space.float_w(w_secs) == 3600.0

    def test_to_s(self, space, monkeypatch):
        monkeypatch.setattr(W_TimeObject, "get_time_struct", self.epoch)
        monkeypatch.setattr(os, "environ", UTC_ENV)
        w_str = space.execute("return Time.now.to_s")
        assert space.str_w(w_str) == "1970-01-01 00:00:00 +0000"
