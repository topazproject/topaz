class TestThreadObject(object):
    def test_name(self, space):
        space.execute("Thread")

    def test_current(self, space):
        w_res = space.execute("return Thread.current.class.name")
        assert space.str_w(w_res) == "Thread"

    def test_thread_local_storage(self, space):
        w_res = space.execute("return Thread.current['a']")
        assert w_res is space.w_nil

        w_res = space.execute("""
        Thread.current["a"] = 1
        return Thread.current[:a]
        """)
        assert space.int_w(w_res) == 1
