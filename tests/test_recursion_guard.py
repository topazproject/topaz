class TestRecursionGuard(object):
    def test_recursion_guard(self, space):
        w_res = space.execute("""
        def foo(objs, depth = 0)
          obj = objs.shift
          recursion = Thread.current.recursion_guard(:foo, obj) do
            return foo(objs, depth + 1)
          end
          if recursion
            return [depth, obj]
          end
        end
        return foo([:a, :b, :c, :a, :d])
        """)
        w_depth, w_symbol = space.listview(w_res)
        assert space.int_w(w_depth) == 3
        assert space.symbol_w(w_symbol) == "a"

    def test_recursion_guard_nested(self, space):
        w_res = space.execute("""
        def foo(objs, depth = 0)
          obj = objs.shift
          Thread.current.recursion_guard(:foo, obj) do
            return bar(objs, depth + 1)
          end
          return [depth, obj]
        end

        def bar(objs, depth)
          obj = objs.shift
          Thread.current.recursion_guard(:bar, obj) do
            return foo(objs, depth + 1)
          end
          return [depth, obj]
        end

        return foo([:a, :a, :b, :b, :c, :a, :d, :d])
        """)
        w_depth, w_symbol = space.listview(w_res)
        assert space.int_w(w_depth) == 5
        assert space.symbol_w(w_symbol) == "a"

    def test_recursion_guard_outer(self, space):
        w_res = space.execute("""
        def foo(objs, depth = 0)
          obj = objs.shift
          Topaz.recursion_guard_outer(:foo, obj) do
            return foo(objs, depth + 1)
          end
          return [depth, obj]
        end
        return foo([:a, :b, :c, :a, :d])
        """)
        w_depth, w_symbol = space.listview(w_res)
        assert space.int_w(w_depth) == 0
        assert space.symbol_w(w_symbol) == "a"
