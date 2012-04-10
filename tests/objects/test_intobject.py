class TestIntObject(object):
    def test_multiplication(self, space, capfd):
        space.execute("puts 2 * 3")
        out, err = capfd.readouterr()
        assert out == "6\n"