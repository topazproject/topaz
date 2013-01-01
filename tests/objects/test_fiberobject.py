from ..base import BaseRuPyPyTest


class TestFiberObject(BaseRuPyPyTest):
    def test_new(self, space):
        space.execute("""
        Fiber.new { }
        """)
        with self.raises(space, "ArgumentError"):
            space.execute("Fiber.new")

    def test_resume(self, space):
        w_res = space.execute("""
        f = Fiber.new { 2 }
        return f.resume
        """)
        assert space.int_w(w_res) == 2

    def test_closure(self, space):
        w_res = space.execute("""
        a = 2
        f = Fiber.new { a = 5 }
        f.resume
        return a
        """)
        assert space.int_w(w_res) == 5

    def test_exception(self, space):
        space.execute("""
        $f = Fiber.new { 1 / 0 }
        """)
        with self.raises(space, "ZeroDivisionError"):
            space.execute("$f.resume")
