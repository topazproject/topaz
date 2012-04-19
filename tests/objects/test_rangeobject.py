import py


class TestRangeObject(object):
    def test_map(self, space):
        w_res = space.execute("""
        return (1..5).map do |x|
            x * 5
        end
        """)
        assert [space.int_w(w_x) for w_x in w_res.items_w] == [5, 10, 15, 20]
