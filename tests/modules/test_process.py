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

    def test_fork(self, space, capfd, monkeypatch):
        # monkeypatch.setattr(os, "fork", lambda: 0)
        w_res = space.execute("""
        begin
            return Process.fork do
                puts "child"
            end
        rescue SystemExit => e
            puts "child exit"
            return nil
        end
        """)
        if w_res is space.w_nil: # Child
            out, err = capfd.readouterr()
            assert out == "child\nchild exit\n"
        else:
            assert isinstance(self.unwrap(space, w_res), int)
