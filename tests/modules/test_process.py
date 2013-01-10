import os

from ..base import BaseTopazTest


class TestProcess(BaseTopazTest):
    def test_pid(self, space):
        w_res = space.execute("return Process.pid")
        assert space.int_w(w_res) == os.getpid()

    def test_exit(self, space):
        with self.raises(space, "SystemExit"):
            space.execute("Process.exit")
        w_res = space.execute("""
        begin
          Process.exit
        rescue SystemExit => e
          return e.success?, e.status
        end
        """)
        assert self.unwrap(space, w_res) == [True, 0]
        w_res = space.execute("""
        begin
          Process.exit(1)
        rescue SystemExit => e
          return e.success?, e.status
        end
        """)
        assert self.unwrap(space, w_res) == [False, 1]
