class TestKernel(object):
    def test_puts_nil(self, space, capfd):
        space.execute("puts nil")
        out, err = capfd.readouterr()
        assert out == "nil\n"