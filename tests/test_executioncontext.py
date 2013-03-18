class TestExecutionContext(object):
    def test_recursion_guard(self, space):
        f = "my_func"
        x = object()
        y = object()
        with space.getexecutioncontext().recursion_guard(f, x) as in_recursion:
            assert not in_recursion
            with space.getexecutioncontext().recursion_guard(f, y) as ir2:
                assert not ir2
                with space.getexecutioncontext().recursion_guard(f, x) as ir3:
                    assert ir3
            with space.getexecutioncontext().recursion_guard(f, x) as ir3:
                assert ir3
