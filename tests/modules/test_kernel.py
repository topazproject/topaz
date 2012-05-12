class TestKernel(object):
    def test_puts_nil(self, ec, capfd):
        ec.space.execute(ec, "puts nil")
        out, err = capfd.readouterr()
        assert out == "nil\n"
