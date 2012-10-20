import py

from ..base import BaseRuPyPyTest


class TestThreadObject(BaseRuPyPyTest):
    def test_name(self, space):
        space.execute("Thread")

    def test_current(self, space):
        w_res = space.execute("return Thread.current.class.name")
        assert space.str_w(w_res) == "Thread"

    @py.test.mark.xfail
    def test_start_doesnt_call_initialize(self, space):
        w_res = space.execute("""
        INITIALIZE_RAN = false
        class X < Thread
           def initialize
             INITIALIZE_RAN = true
             super
           end
        end
        X.start {}
        return INITIALIZE_RAN
        """)
        assert w_res == space.w_false

    @py.test.mark.xfail
    def test_new_calls_initialize(self, space):
        w_res = space.execute("""
        INITIALIZE_RAN = false
        class X < Thread
           def initialize
             INITIALIZE_RAN = true
             super
           end
        end
        X.start {}
        return INITIALIZE_RAN
        """)
        assert w_res == space.w_true

    def test_thread_local_storage(self, space):
        assert space.execute("return Thread.current['a']") == space.w_nil
        w_res = space.execute("""
        Thread.current["a"] = 1
        return Thread.current[:a]
        """)
        assert self.unwrap(space, w_res) == 1
