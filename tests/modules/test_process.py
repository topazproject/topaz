import os

from ..base import BaseTopazTest


class TestProcess(BaseTopazTest):
    def test_euid(self, space):
        w_res = space.execute("return Process.euid")
        assert space.int_w(w_res) == os.geteuid()

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

    def test_fork(self, space, monkeypatch, capfd):
        monkeypatch.setattr(os, "fork", lambda: 0)
        with self.raises(space, "SystemExit"):
            space.execute("""
            Process.fork do
                puts "child"
            end
            """)
        out, err = capfd.readouterr()
        assert err == ""
        assert out == "child\n"
        monkeypatch.setattr(os, "fork", lambda: 200)
        w_res = space.execute("""
        return Process.fork do
            puts "child"
        end
        """)
        assert space.int_w(w_res) == 200

    def test_wait(self, space):
        for code in [0, 1, 173]:
            pid = os.fork()
            if pid == 0:
                os._exit(code)
            else:
                w_res = space.execute("return Process.wait")
                assert space.int_w(w_res) == pid
                w_res = space.execute("return $?")
                status = space.send(w_res, space.newsymbol("to_i"), [])
                assert space.int_w(status) == code
