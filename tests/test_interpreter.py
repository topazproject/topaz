from rupypy.objects.boolobject import W_TrueObject


class TestInterpreter(object):
    def test_add(self, space):
        w_res = space.execute("1 + 1")
        assert isinstance(w_res, W_TrueObject)

    def test_send(self, space, capfd):
        space.execute("puts 1")
        out, err = capfd.readouterr()
        assert out == "1\n"
        assert not err

    def test_variables(self, space, capfd):
        space.execute("a = 100; puts a")
        out, err = capfd.readouterr()
        assert out == "100\n"

    def test_if(self, space, capfd):
        space.execute("if 3 then puts 2 end")
        out, err = capfd.readouterr()
        assert out == "2\n"

        space.execute("x = if 3 then 5 end; puts x")
        out, err = capfd.readouterr()
        assert out == "5\n"

        space.execute("x = if false then 5 end; puts x")
        out, err = capfd.readouterr()
        assert out == "nil\n"

        space.execute("x = if nil then 5 end; puts x")
        out, err = capfd.readouterr()
        assert out == "nil\n"

        space.execute("x = if 3 then end; puts x")
        out, err = capfd.readouterr()
        assert out == "nil\n"