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
