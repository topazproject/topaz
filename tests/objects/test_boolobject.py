class TestTrueObject(object):
    def test_to_s(self, space, capfd):
        space.execute("puts true")
        out, err = capfd.readouterr()
        assert out == "true\n"

class TestFalseObject(object):
    def test_to_s(self, space, capfd):
        space.execute("puts false")
        out, err = capfd.readouterr()
        assert out == "false\n"