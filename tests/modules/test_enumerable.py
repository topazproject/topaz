from ..base import BaseTopazTest


class TestEnumberable(BaseTopazTest):
    def test_inject(self, space):
        w_res = space.execute("""
        return (5..10).inject(1) do |prod, n|
          prod * n
        end
        """)
        assert space.int_w(w_res) == 151200

        w_res = space.execute("""
        return (1..10).inject(0) do |sum, n|
          sum + n
        end
        """)
        assert space.int_w(w_res) == 55

    def test_reduce(self, space):
        w_res = space.execute("""
        return [1, 2, 4, 8].reduce(0) do |accum, cur|
          accum + cur
        end
        """)
        assert space.int_w(w_res) == 15

    def test_each_with_index(self, space):
        w_res = space.execute("""
        result = []
        (5..10).each_with_index do |n, idx|
          result << [n, idx]
        end
        return result
        """)
        assert self.unwrap(space, w_res) == [[5, 0], [6, 1], [7, 2], [8, 3], [9, 4], [10, 5]]

    def test_all(self, space):
        w_res = space.execute("""
        return ["ant", "bear", "cat"].all? do |word|
          word.length > 2
        end
        """)
        assert w_res is space.w_true

    def test_all_false(self, space):
        w_res = space.execute("""
        return ["ant", "bear", "cat"].all? do |word|
          word.length > 3
        end
        """)
        assert w_res is space.w_false

    def test_all_empty(self, space):
        w_res = space.execute("""
        return [].all?
        """)
        assert w_res is space.w_true

    def test_all_no_block(self, space):
        w_res = space.execute("""
        return [1, 2, 3].all?
        """)
        assert w_res is space.w_true

    def test_any(self, space):
        w_res = space.execute("""
        return ["ant", "bear", "cat"].any? do |word|
          word.length > 2
        end
        """)
        assert w_res is space.w_true

    def test_any_false(self, space):
        w_res = space.execute("""
        return [nil, nil, nil].any?
        """)
        assert w_res is space.w_false

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
        w_res = space.execute("""return [0, 1, 2, 3, 4, 5, 6, 7].drop 3""")
        assert self.unwrap(space, w_res) == [3, 4, 5, 6, 7]

        w_res = space.execute("""return [].drop 3""")
        assert self.unwrap(space, w_res) == []

        w_res = space.execute("""return [1, 2, 3].drop 3""")
        assert self.unwrap(space, w_res) == []

        with self.raises(space, "ArgumentError", 'attempt to drop negative size'):
            space.execute("""return [0, 1, 2, 3, 4, 5, 6, 7].drop -3""")

    def test_drop_while(self, space):
        w_res = space.execute("""return [1, 2, 3, 4, 5, 0].drop_while { |i| i < 3 }""")
        assert self.unwrap(space, w_res) == [3, 4, 5, 0]

        w_res = space.execute("""return [1, 2, 3].drop_while { |i| i == 0 } """)
        assert self.unwrap(space, w_res) == [1, 2, 3]

        w_res = space.execute("""return [].drop_while { |i| i > 3 }""")
        assert self.unwrap(space, w_res) == []

    def test_to_a(self, space):
        w_res = space.execute("""return (5..10).to_a""")
        assert self.unwrap(space, w_res) == [x for x in range(5, 11)]

        w_res = space.execute("""return [1, 2, 3, 4].to_a""")
        assert self.unwrap(space, w_res) == [1, 2, 3, 4]

        w_res = space.execute("""
        class A
          include Enumerable

          def each
            i = 0
            while i < 5
              yield i
              i += 1
            end
          end
        end
        return A.new.to_a""")
        assert self.unwrap(space, w_res) == [0, 1, 2, 3, 4]

    def test_detect(self, space):
        w_res = space.execute("return (1..10).detect { |i| i == 11 }")
        assert w_res == space.w_nil
        w_res = space.execute("return (1..10).detect(-1) { |i| i == 11 }")
        assert space.int_w(w_res) == -1
        w_res = space.execute("return (1..10).detect { |i| i == 5 }")
        assert space.int_w(w_res) == 5

    def test_map(self, space):
        w_res = space.execute("return [1, 2, 3, 4, 5].map { |i| i + 1 }")
        assert self.unwrap(space, w_res) == range(2, 7)
        w_res = space.execute("return [1, 2, 3, 4, 5].collect { |i| i + 1 }")
        assert self.unwrap(space, w_res) == range(2, 7)

    def test_take(self, space):
        w_res = space.execute("return [1, 2, 3, 4, 5].take(2)")
        assert self.unwrap(space, w_res) == [1, 2]
        w_res = space.execute("return [1, 2, 3, 4, 5].take(0)")
        assert self.unwrap(space, w_res) == []
        w_res = space.execute("return [].take(2)")
        assert self.unwrap(space, w_res) == []

    def test_take_while(self, space):
        w_res = space.execute("return (1..10).take_while { |i| i < 4 }")
        assert self.unwrap(space, w_res) == [1, 2, 3]
        w_res = space.execute("return [].take_while { |i| i == 11 }")
        assert self.unwrap(space, w_res) == []
        w_res = space.execute("return (1..10).take_while { |i| i > 11 }")
        assert self.unwrap(space, w_res) == []
        w_res = space.execute("return (1..10).take_while { |i| i < 11 }")
        assert self.unwrap(space, w_res) == range(1, 11)

    def test_reject(self, space):
        w_res = space.execute("return [1, 2, 3].reject { |i| i == 3 }")
        assert self.unwrap(space, w_res) == [1, 2]
        w_res = space.execute("return [].reject { |i| i == 3 }")
        assert self.unwrap(space, w_res) == []
        w_res = space.execute("return (1..10).reject { |i| i > 11 }")
        assert self.unwrap(space, w_res) == range(1, 11)
        w_res = space.execute("return (1..10).reject { |i| i < 11 }")
        assert self.unwrap(space, w_res) == []
