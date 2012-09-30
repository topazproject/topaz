from ..base import BaseRuPyPyTest


class TestRangeObject(BaseRuPyPyTest):
    def test_name(self, space):
        space.execute("Range")

    def test_map(self, space):
        w_res = space.execute("""
        return (1..3).map do |x|
            x * 5
        end
        """)
        assert self.unwrap(space, w_res) == [5, 10, 15]

    def test_starting_point_always_returned(self, space):
        w_res = space.execute("""
        return (1..1).map do |x|
            x
        end
        """)
        assert self.unwrap(space, w_res) == [1]

    def test_exclude_end(self, space):
        w_res = space.execute("return (1..5).exclude_end?")
        assert self.unwrap(space, w_res) is False

        w_res = space.execute("return (1...5).exclude_end?")
        assert self.unwrap(space, w_res) is True
