class TestBindingObject(object):
    def test_simple(self, space):
        w_res = space.execute("return binding.eval('4')")
        assert space.int_w(w_res) == 4

    def test_local(self, space):
        w_res = space.execute("""
        a = 4
        return binding.eval('a + 2')
        """)
        assert space.int_w(w_res) == 6

    def test_local_in_binding(self, space):
        w_res = space.execute("""
        a = 5
        return binding.eval('b = 4; a + b')
        """)
        return space.int_w(w_res) == 9

    def test_in_block(self, space):
        w_res = space.execute("""
        def f(a, b)
          return proc { binding }
        end

        return f(3, 4).call.eval("a + b")
        """)
        assert space.int_w(w_res) == 7

    def test_unused_closure(self, space):
        w_res = space.execute("""
        a = 5
        return binding.eval('12')
        """)
        assert space.int_w(w_res) == 12

    def test_local_variable_definedp(self, space):
        w_res = space.execute("""
        a = 5
        return binding.local_variable_defined?('a')
        """)
        assert w_res == space.w_true

    def test_local_variable_get(self, space):
        w_res = space.execute("""
        a = 5
        return binding.local_variable_get('a')
        """)
        assert space.int_w(w_res) == 5

    def test_local_variable_set(self, space):
        w_res = space.execute("""
        a = 5
        binding.local_variable_set('a', 42)
        return a
        """)
        assert space.int_w(w_res) == 42

    def test_local_variables(self, space):
        w_res = space.execute("""
        a = 5
        x = 'foo'
        return binding.local_variables
        """)
        res_w = space.listview(w_res)
        assert space.str_w(res_w[0]) == 'a'
        assert space.str_w(res_w[1]) == 'x'

    def test_receiver(self, space):
        w_res = space.execute("""
        return binding.receiver == self
        """)
        assert w_res == space.w_true
