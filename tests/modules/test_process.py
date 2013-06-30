import os

import pytest

from topaz.modules import process

from ..base import BaseTopazTest


class TestProcess(BaseTopazTest):
    def test_euid(self, space):
        w_res = space.execute("return Process.euid")
        assert space.int_w(w_res) == os.geteuid()

    def test_pid(self, space):
        w_res = space.execute("return Process.pid")
        assert space.int_w(w_res) == os.getpid()
        w_res = space.execute("return $$")
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
        monkeypatch.setattr(process, "fork", lambda: 0)
        with self.raises(space, "SystemExit"):
            space.execute("""
            Process.fork do
              puts "child"
            end
            """)
        out, err = capfd.readouterr()
        assert err == ""
        assert out == "child\n"
        monkeypatch.setattr(process, "fork", lambda: 200)
        w_res = space.execute("""
        return Process.fork do
          puts "child"
        end
        """)
        assert space.int_w(w_res) == 200

    @pytest.mark.parametrize("code", [0, 1, 173])
    def test_waitpid(self, space, code):
        pid = os.fork()
        if pid == 0:
            os._exit(code)
        else:
            w_res = space.execute("return Process.waitpid %i" % pid)
            assert space.int_w(w_res) == pid
            w_res = space.execute("return $?")
            status = space.send(w_res, "to_i", [])
            assert space.int_w(status) == code

    @pytest.mark.parametrize("code", [0, 1, 173])
    def test_waitpid2(self, space, code):
        pid = os.fork()
        if pid == 0:
            os._exit(code)
        else:
            w_res = space.execute("return Process.waitpid2 %i" % pid)
            [returned_pid, returned_code] = space.listview(w_res)
            assert space.int_w(returned_pid) == pid
            code_to_i = space.send(returned_code, "to_i", [])
            assert space.int_w(code_to_i) == code
