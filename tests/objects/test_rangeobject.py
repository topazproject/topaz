from ..base import BaseRuPyPyTest


class TestRangeObject(BaseRuPyPyTest):
    def test_map(self, space):
        w_res = space.execute("""
        return (1..3).map do |x|
            x * 5
        end
        """)
        assert self.unwrap(space, w_res) == [5, 10]

    def test_starting_point_always_returned(self, space):
        w_res = space.execute("""
        return (1..1).map do |x|
            x
        end
        """)
        assert self.unwrap(space, w_res) == [1]
