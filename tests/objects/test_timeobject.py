import time

import pytest


# pytest currently explodes with monkeypatching time.time
@pytest.mark.xfail(run=False)
class TestTimeObject(object):
    def test_now(self, space, monkeypatch):
        monkeypatch.setattr(time, "time", lambda: 342.1)
        w_secs = space.execute("return Time.now.to_f")
        assert space.float_w(w_secs) == 342.1

    def test_subtraction(self, space, monkeypatch):
        monkeypatch.setattr(time, "time", iter([18, 12]).next)
        w_secs = space.execute("return Time.now - Time.now")
        assert space.float_w(w_secs) == 6
