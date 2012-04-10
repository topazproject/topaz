class TestIntObject(object):
    def test_multiplication(self, space, capfd):
        space.execute("puts 2 * 3")
        out, err = capfd.readouterr()
        assert out == "6\n"

    def test_subtraction(self, space, capfd):
        space.execute("puts 2 - 3")
        out, err = capfd.readouterr()
        assert out == "-1\n"

    def test_equal(self, space, capfd):
        space.execute("puts 1 == 1")
        out, err = capfd.readouterr()
        assert out == "true\n"

    def test_not_equal(self, space, capfd):
        space.execute("puts 1 != 1")
        out, err = capfd.readouterr()
        assert out == "false\n"

    def test_less(self, space, capfd):
        space.execute("puts 1 < 2")
        out, err = capfd.readouterr()
        assert out == "true\n"