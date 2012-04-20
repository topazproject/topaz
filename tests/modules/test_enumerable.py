class TestKernel(object):
    def test_inject(self, space):
        w_res = space.execute("""
        return (5..10).inject(1) do |prod, n|
            prod * n
        end
        """)
        assert space.int_w(w_res) == 15120

        w_res = space.execute("""
        return (1..10).inject 0 do |sum, n|
            sum + n
        end
        """)
        assert space.int_w(w_res) == 45