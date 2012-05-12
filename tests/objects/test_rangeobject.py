class TestRangeObject(object):
    def test_map(self, ec):
        w_res = ec.space.execute(ec, """
        return (1..3).map do |x|
            x * 5
        end
        """)
        assert [ec.space.int_w(w_x) for w_x in ec.space.listview(w_res)] == [5, 10]

    def test_starting_point_always_returned(self, ec):
        w_res = ec.space.execute(ec, """
        return (1..1).map do |x|
            x
        end
        """)
        assert [ec.space.int_w(w_x) for w_x in ec.space.listview(w_res)] == [1]
