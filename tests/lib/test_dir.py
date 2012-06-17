import os


class TestDir(object):
    def test_name(self, space):
        space.execute("Dir")

    def test_pwd(self, space):
        w_res = space.execute("return Dir.pwd")
        assert space.str_w(w_res) == os.getcwd()
