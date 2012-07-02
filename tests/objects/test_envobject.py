import os

from rupypy.objects.objectobject import W_Object

from ..base import BaseRuPyPyTest


class TestEnvObject(BaseRuPyPyTest):
    def test_class(self, space):
        w_res = space.execute("return ENV.class")
        assert w_res == self.find_const(space, "Object")

    def test_access_env(self, space, monkeypatch):
        env = {"HOME": "/home/test"}
        monkeypatch.setattr(os, 'environ', env)

        w_res = space.execute("return ENV['HOME']")
        assert space.str_w(w_res) == "/home/test"
        w_res = space.execute("return ENV['HEIM']")
        assert w_res == space.w_nil
        w_res = space.execute("""
        ENV['HOME'] = '/home/newhome'
        return ENV['HOME']
        """)
        assert space.str_w(w_res) == "/home/newhome"
        assert env["HOME"] == "/home/newhome"
