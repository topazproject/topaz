# coding=utf-8

import struct

from ..base import BaseTopazTest


class TestArrayObject(BaseTopazTest):
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
        w_res = space.execute("a = []; a[0, 0] = [3, 4, 5]; return a")
        assert self.unwrap(space, w_res) == [3, 4, 5]
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
        with self.raises(space, "TypeError", "can't convert Symbol into Array"):
            space.execute("[1, 2] + :not_an_array")
        w_res = space.execute("""
        class NotAnArray
          def to_ary
            [8, 7]
          end
        end
        return [9] + NotAnArray.new
        """)
        assert self.unwrap(space, w_res) == [9, 8, 7]

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
        w_res = space.execute("x = [1, 2, 3]; x[1..-2] = []; return x")
        assert self.unwrap(space, w_res) == [1, 3]
        w_res = space.execute("x = [1, 2, 3]; x[1..-2] = [4]; return x")
        assert self.unwrap(space, w_res) == [1, 4, 3]
        w_res = space.execute("x = [1, 2, 3]; x[1..-2] = [4, 5]; return x")
        assert self.unwrap(space, w_res) == [1, 4, 5, 3]

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
            space.execute("[1].join(:foo)")
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
        assert self.unwrap(space, space.execute("return [].pop")) is None
        with self.raises(space, "ArgumentError"):
            space.execute("[1].pop(-1)")
        with self.raises(space, "TypeError"):
            space.execute("[1].pop('a')")

    def test_delete(self, space):
        w_res = space.execute("""
        a = [ "a", "b", "b", "b", "c" ]
        r = []
        r << a.delete("b")
        r << a
        r << a.delete("z")
        r << a.delete("z") { "not found" }
        return r
        """)
        assert self.unwrap(space, w_res) == ["b", ["a", "c"], None, "not found"]

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

    def test_first(self, space):
        assert space.int_w(space.execute("return [1, 2, 3].first")) == 1
        assert space.execute("return [].first") == space.w_nil

    def test_last(self, space):
        assert space.int_w(space.execute("return [1, 2, 3].last")) == 3
        assert space.execute("return [].last") == space.w_nil

    def test_shift(self, space):
        w_res = space.execute("return [].shift")
        assert w_res is space.w_nil

        w_res = space.execute("""
        a = [1, 2]
        return [a.shift, a]
        """)
        assert self.unwrap(space, w_res) == [1, [2]]

        w_res = space.execute("""
        a = [1, 2, 3, 4, 5]
        return [a.shift(2), a]
        """)
        assert self.unwrap(space, w_res) == [[1, 2], [3, 4, 5]]

        with self.raises(space, "ArgumentError"):
            space.execute("[].shift(-2)")

    def test_push(self, space):
        w_res = space.execute("return [].push(2, 3)")
        assert self.unwrap(space, w_res) == [2, 3]

    def test_eq(self, space):
        w_res = space.execute("""
        x = []
        return [
          [] == :abc,
          [] == [],
          [:abc] == [:abc],
          x == (x << 2),
          [1, 2, 3] == [1, 2, 4],
          [1] == [1, 2],
        ]
        """)
        assert self.unwrap(space, w_res) == [False, True, True, True, False, False]

    def test_eqlp(self, space):
        w_res = space.execute("return [].eql? 2")
        assert w_res is space.w_false
        w_res = space.execute("return [0].eql? [0.0]")
        assert w_res is space.w_false
        w_res = space.execute("return [0].eql? [0]")
        assert w_res is space.w_true

    def test_clear(self, space):
        w_res = space.execute("""
        a = [1, 2, 3]
        a.clear
        return a
        """)
        assert self.unwrap(space, w_res) == []

    def test_hashability(self, space):
        w_res = space.execute("return {[] => 2}[[]]")
        assert space.int_w(w_res) == 2
        w_res = space.execute("return {[1] => 5}[[1]]")
        assert space.int_w(w_res) == 5
        w_res = space.execute("return {[1, 2, 3] => 5}[[1, 2]]")
        assert w_res is space.w_nil

    def test_sort(self, space):
        w_res = space.execute("""
        a = [3, 2, 1]
        b = a.sort
        return a.object_id == b.object_id, a, b
        """)
        assert self.unwrap(space, w_res) == [False, [3, 2, 1], [1, 2, 3]]
        w_res = space.execute("""
        a = [3, 2, 1]
        b = a.sort!
        return a.object_id == b.object_id, a, b
        """)
        assert self.unwrap(space, w_res) == [True, [1, 2, 3], [1, 2, 3]]
        w_res = space.execute("""
        a = [1, 2, 3]
        b = a.sort { |a, b| -a <=> -b }
        return a.object_id == b.object_id, a, b
        """)
        assert self.unwrap(space, w_res) == [False, [1, 2, 3], [3, 2, 1]]
        w_res = space.execute("""
        a = [1, 2, 3]
        b = a.sort! { |a, b| -a <=> -b }
        return a.object_id == b.object_id, a, b
        """)
        assert self.unwrap(space, w_res) == [True, [3, 2, 1], [3, 2, 1]]
        with self.raises(space, "NoMethodError"):
            space.execute("[0, 1].sort{ |n, m| BasicObject.new }")
        with self.raises(space, "ArgumentError", "comparison of Array with Object failed"):
            space.execute("[Object.new, []].sort")

    def test_multiply(self, space):
        w_res = space.execute("return [ 1, 2, 3 ] * 3")
        assert self.unwrap(space, w_res) == [1, 2, 3, 1, 2, 3, 1, 2, 3]
        w_res = space.execute("return [ 1, 2, 3 ] * ','")
        assert self.unwrap(space, w_res) == "1,2,3"

    def test_flatten(self, space):
        w_res = space.execute("""
        s = [ 1, 2, 3 ]
        t = [ 4, 5, 6, [7, 8] ]
        a = [ s, t, 9, 10 ]
        return a.flatten
        """)
        assert self.unwrap(space, w_res) == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        w_res = space.execute("return [ 1, 2, [3, [4, 5] ] ].flatten(1)")
        assert self.unwrap(space, w_res) == [1, 2, 3, [4, 5]]
        with self.raises(space, "ArgumentError", "tried to flatten recursive array"):
            space.execute("""
            a = [0, 1, 2, 3]
            a[0] = a
            a.flatten
            """)


class TestArrayPack(BaseTopazTest):
    def test_garbage_format(self, space):
        assert space.str_w(space.execute("return [].pack ''")) == ""
        assert space.str_w(space.execute("return [].pack 'yy'")) == ""
        assert space.str_w(space.execute("return [1, 2].pack 'y3'")) == ""

    def test_padding(self, space):
        assert space.str_w(space.execute("return [].pack 'xx'")) == "\0\0"
        assert space.str_w(space.execute("return [].pack 'x2'")) == "\0\0"

    def test_moving(self, space):
        assert space.str_w(space.execute("return [].pack '@2'")) == "\0\0"
        assert space.str_w(space.execute("return [].pack 'xx@2'")) == "\0\0"

    def test_backing_up(self, space):
        assert space.str_w(space.execute("return [].pack 'xxXX'")) == ""
        with self.raises(space, "ArgumentError", "X outside of string"):
            space.execute("[].pack 'X'")

    def test_char(self, space):
        assert space.str_w(space.execute("return [-10, 10].pack 'cc'")) == struct.pack("bb", -10, 10)
        assert space.str_w(space.execute("return [255].pack 'C'")) == struct.pack("B", 255)
        assert space.str_w(space.execute("return [256].pack 'C'")) == struct.pack("B", 256 % 256)
        assert space.str_w(space.execute("return [-255].pack 'C'")) == struct.pack("B", -255 % 256)
        with self.raises(space, "ArgumentError", "> allowed only after types SsIiLlQq"):
            space.execute("[-255].pack 'C>'")
        with self.raises(space, "ArgumentError", "! allowed only after types SsIiLl"):
            space.execute("[-255].pack 'C!'")
        with self.raises(space, "ArgumentError", "< allowed only after types SsIiLlQq"):
            space.execute("[-255].pack 'C<'")

    def test_short(self, space):
        assert space.str_w(space.execute("return [-255].pack 'S'")) == struct.pack("H", -255 % 2 ** 16)
        assert space.str_w(space.execute("return [12].pack 's'")) == struct.pack("h", 12)
        assert space.str_w(space.execute("return [12].pack 'S!'")) == struct.pack("@h", 12)
        assert space.str_w(space.execute("return [12].pack 'S_'")) == struct.pack("@h", 12)
        assert space.str_w(space.execute("return [12].pack 'S_!_'")) == struct.pack("@h", 12)
        with self.raises(space, "RangeError", "Can't use both '<' and '>'"):
            space.execute("[2].pack 'S><'")

    def test_long(self, space):
        assert space.str_w(space.execute("return [-255].pack 'I'")) == struct.pack("I", -255 % 2 ** 32)
        assert space.str_w(space.execute("return [12].pack 'i'")) == struct.pack("i", 12)
        assert space.str_w(space.execute("return [-255].pack 'L'")) == struct.pack("I", -255 % 2 ** 32)
        assert space.str_w(space.execute("return [12].pack 'l'")) == struct.pack("i", 12)

    def test_longlong(self, space):
        assert space.str_w(space.execute("return [-255].pack 'Q'")) == struct.pack("Q", -255 % 2 ** 64)
        assert space.str_w(space.execute("return [12].pack 'q'")) == struct.pack("q", 12)

    def test_float(self, space):
        assert space.str_w(space.execute("return [-255].pack 'f'")) == struct.pack("f", -255)
        assert space.str_w(space.execute("return [-255].pack 'F'")) == struct.pack("f", -255)
        assert space.str_w(space.execute("return [-255.42].pack 'F'")) == struct.pack("f", -255.42)

    def test_double(self, space):
        assert space.str_w(space.execute("return [-255].pack 'd'")) == struct.pack("d", -255)
        assert space.str_w(space.execute("return [-255].pack 'D'")) == struct.pack("d", -255)
        assert space.str_w(space.execute("return [-255.42].pack 'D'")) == struct.pack("d", -255.42)

    def test_strings(self, space):
        string = "abö"
        assert space.str_w(space.execute("return ['%s'].pack 'a'" % string)) == string[0]
        assert space.str_w(space.execute("return ['%s'].pack 'A6'" % string)) == string + "  "
        assert space.str_w(space.execute("return ['abö'].pack 'a6'")) == string + "\0\0"
        assert space.str_w(space.execute("return ['abö'].pack 'Z6'")) == string + "\0\0"
        assert space.str_w(space.execute("return ['abö'].pack 'Z*'")) == string + "\0"

    def test_endianess(self, space):
        assert space.str_w(space.execute("return [42].pack 's<'")) == struct.pack("<h", 42)
        assert space.str_w(space.execute("return [42].pack 's>'")) == struct.pack(">h", 42)
        assert space.str_w(space.execute("return [42].pack 'S<'")) == struct.pack("<H", 42)
        assert space.str_w(space.execute("return [42].pack 'S>'")) == struct.pack(">H", 42)

        assert space.str_w(space.execute("return [42].pack 'i<'")) == struct.pack("<i", 42)
        assert space.str_w(space.execute("return [42].pack 'i>'")) == struct.pack(">i", 42)
        assert space.str_w(space.execute("return [42].pack 'I<'")) == struct.pack("<I", 42)
        assert space.str_w(space.execute("return [42].pack 'I>'")) == struct.pack(">I", 42)

        assert space.str_w(space.execute("return [42].pack 'q<'")) == struct.pack("<q", 42)
        assert space.str_w(space.execute("return [42].pack 'q>'")) == struct.pack(">q", 42)
        assert space.str_w(space.execute("return [42].pack 'Q<'")) == struct.pack("<Q", 42)
        assert space.str_w(space.execute("return [42].pack 'Q>'")) == struct.pack(">Q", 42)

        assert space.str_w(space.execute("return [42].pack 'v'")) == struct.pack("<H", 42)
        assert space.str_w(space.execute("return [42].pack 'V'")) == struct.pack("<I", 42)
        assert space.str_w(space.execute("return [42].pack 'n'")) == struct.pack(">H", 42)
        assert space.str_w(space.execute("return [42].pack 'N'")) == struct.pack(">I", 42)

        assert space.str_w(space.execute("return [4.2].pack 'e'")) == struct.pack("<f", 4.2)
        assert space.str_w(space.execute("return [4.2].pack 'g'")) == struct.pack(">f", 4.2)
        assert space.str_w(space.execute("return [4.2].pack 'E'")) == struct.pack("<d", 4.2)
        assert space.str_w(space.execute("return [4.2].pack 'G'")) == struct.pack(">d", 4.2)

    def test_complex(self, space):
        w_res = space.execute("""
        return [65, 66, 5, 5, 4.2, 4.2, "hello"].pack 'c02s<s>egg0Z*'
        """)
        expected = (struct.pack("2b", 65, 66) +
                    struct.pack("<h", 5) +
                    struct.pack(">h", 5) +
                    struct.pack("<f", 4.2) +
                    struct.pack(">f", 4.2) +
                    "hello\0")
        assert space.str_w(w_res) == expected

    def test_pointers(self, space):
        pointerlen = struct.calcsize("P")
        w_res = space.execute("return [''].pack 'P'")
        assert space.str_w(w_res) == "\0" * pointerlen
        w_res = space.execute("return [''].pack 'p'")
        assert space.str_w(w_res) == "\0" * pointerlen

    def test_errors(self, space):
        with self.raises(space, "ArgumentError", "too few arguments"):
            space.execute("[].pack 'P'")
        with self.raises(space, "ArgumentError", "too few arguments"):
            space.execute("[].pack 'a'")
        with self.raises(space, "ArgumentError", "too few arguments"):
            space.execute("[].pack 'c'")
        with self.raises(space, "ArgumentError", "too few arguments"):
            space.execute("[].pack 'f'")
        with self.raises(space, "RangeError", "pack length too big"):
            space.execute("[].pack 'a18446744073709551617'")

    def test_max(self, space):
        w_res = space.execute("""
        a = %w(albatross dog horse)
        return a.max
        """)
        assert self.unwrap(space, w_res) == "horse"
        w_res = space.execute("""
        a = %w(albatross dog horse)
        return a.max { |a, b| a.length <=> b.length }
        """)
        assert self.unwrap(space, w_res) == "albatross"
        assert space.execute("[].max") is space.w_nil

    def test_singleton_subscript(self, space):
        w_res = space.execute("return Array[6, -1]")
        assert self.unwrap(space, w_res) == [6, -1]

    def test_each(self, space):
        w_res = space.execute("return [1, 2].each { }")
        assert self.unwrap(space, w_res) == [1, 2]
