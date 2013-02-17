class TestExecutionContext(object):
    def test_recursion_guard(self, space):
        x = object()
        y = object()
        with space.getexecutioncontext().recursion_guard(x) as in_recursion:
            assert not in_recursion
            with space.getexecutioncontext().recursion_guard(y) as ir2:
                assert not ir2
                with space.getexecutioncontext().recursion_guard(x) as ir3:
                    assert ir3
            with space.getexecutioncontext().recursion_guard(x) as ir3:
                assert ir3
