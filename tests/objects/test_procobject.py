from ..base import BaseTopazTest


class TestProcObject(BaseTopazTest):
    def test_new(self, space):
        w_res = space.execute("""
        p = Proc.new { foo }
        return [p.class, p.lambda?]
        """)
        w_cls, w_proc = space.listview(w_res)
        assert w_cls is space.w_proc
        assert w_proc is space.w_false

    def test_call(self, space):
        w_res = space.execute("""
        p = proc { 1 }
        return [p.call, p[]]
        """)
        assert self.unwrap(space, w_res) == [1, 1]

    def test_return(self, space):
        w_res = space.execute("""
        def f(a)
          a << "a"
          a << (lambda { return "r" }.call)
          a << "b"
          proc { return "p" }.call
          a << "f"
        end

        a = []
        a << (f(a))
        return a
        """)
        assert self.unwrap(space, w_res) == ["a", "r", "b", "p"]

    def test_break(self, space):
        w_res = space.execute("""
        return lambda { break 3 }.call
        """)
        assert space.int_w(w_res) == 3
        with self.raises(space, "LocalJumpError"):
            space.execute("""
            proc { break }.call
            """)

    def test_binding(self, space):
        w_res = space.execute("""
        def f(a)
          return proc {}
        end
        return f(2).binding.eval("a")
        """)
        assert space.int_w(w_res) == 2
