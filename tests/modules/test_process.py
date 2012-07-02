import os

from ..base import BaseRuPyPyTest


class TestProcess(BaseRuPyPyTest):
    def test_pid(self, space):
        w_res = space.execute("return Process.pid")
        assert space.int_w(w_res) == os.getpid()
