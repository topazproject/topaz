class TestRangeObject(object):
    def test_map(self, space):
        w_res = space.execute("""
        return (1..3).map do |x|
            x * 5
        end
        """)
        assert [space.int_w(w_x) for w_x in space.listview(w_res)] == [5, 10]

    def test_starting_point_always_returned(self, space):
        w_res = space.execute("""
        return (1..1).map do |x|
            x
        end
        """)
        assert [space.int_w(w_x) for w_x in space.listview(w_res)] == [1]
