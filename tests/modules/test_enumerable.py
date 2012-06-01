class TestEnumberable(object):
    def test_inject(self, ec):
        w_res = ec.space.execute(ec, """
        return (5..10).inject(1) do |prod, n|
            prod * n
        end
        """)
        assert ec.space.int_w(w_res) == 15120

        w_res = ec.space.execute(ec, """
        return (1..10).inject 0 do |sum, n|
            sum + n
        end
        """)
        assert ec.space.int_w(w_res) == 45

    def test_each_with_index(self, ec):
        w_res = ec.space.execute(ec, """
        result = []
        (5..10).each_with_index do |n, idx|
            result << [n, idx]
        end
        return result
        """)
        assert [[ec.space.int_w(w_x) for w_x in ec.space.listview(w_sub)] for w_sub in ec.space.listview(w_res)] == [[5, 0], [6, 1], [7, 2], [8, 3], [9, 4]]
