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

    def test_select(self, space):
        w_res = space.execute("""
        return (2..4).select { |x| x == 2 }
        """)
        assert self.unwrap(space, w_res) == [2]

    def test_include(self, space):
        w_res = space.execute("""
        return (2..5).include? 12
        """)
        assert w_res is space.w_false

        w_res = space.execute("""
        return (2..3).include? 2
        """)
        assert w_res is space.w_true

    def test_drop(self, space):
        w_res = space.execute("""return [0,1,2,3,4,5,6,7].drop 3""")
        assert self.unwrap(space, w_res) == [3,4,5,6,7]

        w_res = space.execute("""return [].drop 3""")
        assert self.unwrap(space, w_res) == []

        w_res = space.execute("""return [1, 2, 3].drop 3""")
        assert self.unwrap(space, w_res) == []

        with self.raises("ArgumentError", 'attempt to drop negative size'):
            space.execute("""return [0,1,2,3,4,5,6,7].drop -3""")
