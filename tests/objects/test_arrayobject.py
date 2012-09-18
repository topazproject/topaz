from ..base import BaseRuPyPyTest


class TestArrayObject(BaseRuPyPyTest):
    def test_to_s(self, space):
        w_res = space.execute("return [].to_s")
        assert space.str_w(w_res) == "[]"

        w_res = space.execute("return [[1]].to_s")
        assert space.str_w(w_res) == "[[1]]"

        w_res = space.execute("return [[1], [2], [3]].to_s")
        assert space.str_w(w_res) == "[[1], [2], [3]]"

    def test_subscript(self, space):
        w_res = space.execute("return [1][0]")
        assert space.int_w(w_res) == 1
        w_res = space.execute("return [1].at(0)")
        assert space.int_w(w_res) == 1
        w_res = space.execute("return [1][1]")
        assert w_res is space.w_nil
        w_res = space.execute("return [1][-1]")
        assert space.int_w(w_res) == 1
        w_res = space.execute("return [1][-2]")
        assert w_res == space.w_nil
        w_res = space.execute("return [1, 2][0, 0]")
        assert self.unwrap(space, w_res) == []
        w_res = space.execute("return [1, 2][0, 1]")
        assert self.unwrap(space, w_res) == [1]
        w_res = space.execute("return [1, 2][0, 5]")
        assert self.unwrap(space, w_res) == [1, 2]
        w_res = space.execute("return [1, 2][0, -1]")
        assert w_res is space.w_nil
        w_res = space.execute("return [1, 2][-1, 1]")
        assert self.unwrap(space, w_res) == [2]
        w_res = space.execute("return [1, 2][-2, 2]")
        assert self.unwrap(space, w_res) == [1, 2]
        w_res = space.execute("return [1, 2][-2, 2]")
        assert self.unwrap(space, w_res) == [1, 2]
        with self.raises(space, "TypeError"):
            space.execute("[1, 2][1..2, 1]")
        w_res = space.execute("""
        class String; def to_int; 1; end; end
        return [1, 2]["1", "1"]
        """)
        assert self.unwrap(space, w_res) == [2]

    def test_subscript_assign(self, space):
        w_res = space.execute("a = [1]; a[0] = 42; return a")
        assert self.unwrap(space, w_res) == [42]
        w_res = space.execute("a = [1]; a[1] = 42; return a")
        assert self.unwrap(space, w_res) == [1, 42]
        w_res = space.execute("a = [1]; a[-1] = 42; return a")
        assert self.unwrap(space, w_res) == [42]
        with self.raises(space, "IndexError", "index -2 too small for array; minimum: -1"):
            space.execute("a = [1]; a[-2] = 42")
        w_res = space.execute("a = [1, 2]; a[0, 0] = 42; return a")
        assert self.unwrap(space, w_res) == [42, 1, 2]
        w_res = space.execute("a = [1, 2]; a[0, 1] = 42; return a")
        assert self.unwrap(space, w_res) == [42, 2]
        w_res = space.execute("a = [1, 2]; a[0, 5] = 42; return a")
        assert self.unwrap(space, w_res) == [42]
        with self.raises(space, "IndexError", "negative length (-1)"):
            w_res = space.execute("a = [1, 2]; a[0, -1] = 42")
        w_res = space.execute("a = [1, 2]; a[-1, 1] = 42; return a")
        assert self.unwrap(space, w_res) == [1, 42]
        w_res = space.execute("a = [1, 2]; a[-2, 2] = 42; return a")
        assert self.unwrap(space, w_res) == [42]

    def test_length(self, space):
        w_res = space.execute("return [1, 2, 3].length")
        assert space.int_w(w_res) == 3

    def test_emptyp(self, space):
        w_res = space.execute("return [].empty?")
        assert w_res is space.w_true
        w_res = space.execute("return [1].empty?")
        assert w_res is space.w_false

    def test_plus(self, space):
        w_res = space.execute("return [1, 2] + [3]")
        assert self.unwrap(space, w_res) == [1, 2, 3]

    def test_minus(self, space):
        w_res = space.execute("return [1, 1, 2, '3'] - [1, '3']")
        assert self.unwrap(space, w_res) == [2]

    def test_lshift(self, space):
        w_res = space.execute("return [] << 1")
        assert self.unwrap(space, w_res) == [1]

    def test_concat(self, space):
        w_res = space.execute("""
        a = [1, 2]
        b = a.concat([3, 4])
        return a, a == b
        """)
        assert self.unwrap(space, w_res) == [[1, 2, 3, 4], True]

    def test_zip(self, space):
        w_res = space.execute("return [1, 2, 3].zip([3, 2, 1])")
        assert self.unwrap(space, w_res) == [[1, 3], [2, 2], [3, 1]]

    def test_product(self, space):
        w_res = space.execute("return [1, 2].product([3, 4])")
        assert self.unwrap(space, w_res) == [[1, 3], [1, 4], [2, 3], [2, 4]]

    def test_size(self, space):
        w_res = space.execute("return [1, 2].size")
        assert space.int_w(w_res) == 2

    def test_range_inclusive(self, space):
        w_res = space.execute("return [1, 2, 3, 4, 5][1..2]")
        assert self.unwrap(space, w_res) == [2, 3]
        w_res = space.execute("return [1, 2, 3, 4, 5][1..-1]")
        assert self.unwrap(space, w_res) == [2, 3, 4, 5]
        w_res = space.execute("return [1, 2, 3, 4, 5][-2..-1]")
        assert self.unwrap(space, w_res) == [4, 5]
        w_res = space.execute("return [][-1..-2]")
        assert w_res == space.w_nil
        w_res = space.execute("return [][0..-2]")
        assert self.unwrap(space, w_res) == []
        w_res = space.execute("return [1, 2][-1..-2]")
        assert self.unwrap(space, w_res) == []
        w_res = space.execute("""
        class String; def to_int; 1; end; end
        return [1, 2, 3, 4, 5]["1".."1"]
        """)
        assert self.unwrap(space, w_res) == [2]

    def test_range_exclusive(self, space):
        w_res = space.execute("return [1, 2, 3, 4, 5][1...3]")
        assert self.unwrap(space, w_res) == [2, 3]
        w_res = space.execute("return [1, 2, 3, 4, 5][1...-1]")
        assert self.unwrap(space, w_res) == [2, 3, 4]
        w_res = space.execute("return [1, 2, 3, 4, 5][-2...-1]")
        assert self.unwrap(space, w_res) == [4]

    def test_range_assignment(self, space):
        w_res = space.execute("x = [1, 2, 3]; x[1..2] = 4; return x")
        assert self.unwrap(space, w_res) == [1, 4]
        w_res = space.execute("x = [1, 2, 3]; x[1..-2] = 4; return x")
        assert self.unwrap(space, w_res) == [1, 4, 3]
        w_res = space.execute("x = [1, 2, 3]; x[-3..-2] = 4; return x")
        assert self.unwrap(space, w_res) == [4, 3]
        w_res = space.execute("x = [1, 2, 3]; x[-1..-2] = 4; return x")
        assert self.unwrap(space, w_res) == [1, 2, 4, 3]

    def test_at(self, space):
        w_res = space.execute("return [1, 2, 3, 4, 5].at(2)")
        assert space.int_w(w_res) == 3

    def test_unshift(self, space):
        w_res = space.execute("return [1, 2].unshift(3, 4)")
        assert self.unwrap(space, w_res) == [3, 4, 1, 2]

    def test_join(self, space):
        w_res = space.execute("return [1, 'a', :b].join")
        assert space.str_w(w_res) == "1ab"
        w_res = space.execute("return [1, 'a', :b].join('--')")
        assert space.str_w(w_res) == "1--a--b"
        w_res = space.execute("return [1, 'a', :b].join(?-)")
        assert space.str_w(w_res) == "1-a-b"
        with self.raises(space, "TypeError", "can't convert Symbol into String"):
            space.execute("return [1].join(:foo)")
        w_res = space.execute("return [].join(:foo)")
        assert space.str_w(w_res) == ""
        w_res = space.execute("""
        class A; def to_str; 'A'; end; end
        return [1, 2].join(A.new)
        """)
        assert space.str_w(w_res) == "1A2"

    def test_dup(self, space):
        w_res = space.execute("""
        x = [1, 2, 3]
        y = x.dup
        x << 4
        return [x, y]
        """)
        x, y = self.unwrap(space, w_res)
        assert x == [1, 2, 3, 4]
        assert y == [1, 2, 3]

    def test_compact(self, space):
        w_res = space.execute("return ['a', nil, 'b', nil, 'c'].compact")
        assert self.unwrap(space, w_res) == ['a', 'b', 'c']

    def test_rejectbang(self, space):
        w_res = space.execute("return [1, 2, 3, 4].reject! { false }")
        assert w_res == space.w_nil
        w_res = space.execute("return [1, 2, 3, 4].reject! { true }")
        assert space.listview(w_res) == []

    def test_delete_if(self, space):
        w_res = space.execute("""
        a = [1, 2, 3]
        a.delete_if { true }
        return a
        """)
        assert self.unwrap(space, w_res) == []
        w_res = space.execute("""
        a = [1, 2, 3, 4]
        return a.delete_if {|x| x > 2 }
        """)
        assert self.unwrap(space, w_res) == [1, 2]
        w_res = space.execute("""
        a = [1, 2, 3, 4]
        return a.delete_if {|x| x == 2 || x == 4 }
        """)
        assert self.unwrap(space, w_res) == [1, 3]
        w_res = space.execute("""
        a = [1, 2, 3, 4]
        return a.delete_if {|x| x == 1 || x == 3 }
        """)
        assert self.unwrap(space, w_res) == [2, 4]

    def test_pop(self, space):
        assert self.unwrap(space, space.execute("return [1, 2, 3].pop")) == 3
        assert self.unwrap(space, space.execute("return [1, 2, 3].pop(0)")) == []
        assert self.unwrap(space, space.execute("return [1, 2, 3].pop(1)")) == [3]
        assert self.unwrap(space, space.execute("return [1, 2, 3].pop(2)")) == [2, 3]
        assert self.unwrap(space, space.execute("return [1, 2, 3].pop(10)")) == [1, 2, 3]
        assert self.unwrap(space, space.execute("return [].pop(1)")) == []
        assert self.unwrap(space, space.execute("return [].pop")) == None
        with self.raises(space, "ArgumentError"):
            space.execute("return [1].pop(-1)")
        with self.raises(space, "TypeError"):
            space.execute("return [1].pop('a')")

    def test_delete_at(self, space):
        w_res = space.execute("""
        res = []
        a = ["ant", "bat", "cat", "dog"]
        res << a.delete_at(2)    #=> "cat"
        res << a                 #=> ["ant", "bat", "dog"]
        res << a.delete_at(99)   #=> nil
        return res
        """)
        assert self.unwrap(space, w_res) == ["cat", ["ant", "bat", "dog"], None]

    def test_last(self, space):
        assert space.int_w(space.execute("return [1, 2, 3].last")) == 3
        assert space.execute("return [].last") == space.w_nil
