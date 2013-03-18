from ..base import BaseTopazTest


class TestFiberObject(BaseTopazTest):
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

    def test_nested_resume(self, space):
        with self.raises(space, "FiberError", "double resume"):
            space.execute("""
            f = Fiber.new {
                f.resume
            }
            f.resume
            """)

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

    def test_yield(self, space):
        w_res = space.execute("""
        r = []
        f = Fiber.new {
            r << 1
            Fiber.yield 3
            r << 2
        }
        r << "a"
        res = f.resume
        r << res
        r << "b"
        f.resume
        r << "c"
        return r
        """)
        assert self.unwrap(space, w_res) == ["a", 1, 3, "b", 2, "c"]
