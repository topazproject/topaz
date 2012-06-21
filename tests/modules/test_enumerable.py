from ..base import BaseRuPyPyTest


class TestEnumberable(BaseRuPyPyTest):
    def test_inject(self, space):
        w_res = space.execute("""
        return (5..10).inject(1) do |prod, n|
            prod * n
        end
        """)
        assert space.int_w(w_res) == 151200

        w_res = space.execute("""
        return (1..10).inject 0 do |sum, n|
            sum + n
        end
        """)
        assert space.int_w(w_res) == 55

    def test_each_with_index(self, space):
        w_res = space.execute("""
        result = []
        (5..10).each_with_index do |n, idx|
            result << [n, idx]
        end
        return result
        """)
        assert self.unwrap(space, w_res) == [[5, 0], [6, 1], [7, 2], [8, 3], [9, 4], [10, 5]]
