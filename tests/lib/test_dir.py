import os


class TestDir(object):
    def test_name(self, ec):
        ec.space.execute(ec, "Dir")

    def test_pwd(self, ec):
        w_res = ec.space.execute(ec, "return Dir.pwd")
        assert ec.space.str_w(w_res) == os.getcwd()
