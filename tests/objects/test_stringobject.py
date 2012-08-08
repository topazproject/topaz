from ..base import BaseRuPyPyTest


class TestStringObject(BaseRuPyPyTest):
    def test_lshift(self, space):
        w_res = space.execute('return "abc" << "def" << "ghi"')
        assert space.str_w(w_res) == "abcdefghi"

    def test_plus(self, space):
        w_res = space.execute('return "abc" + "def" + "ghi"')
        assert space.str_w(w_res) == "abcdefghi"

    def test_to_s(self, space):
        w_res = space.execute('return "ABC".to_s')
        assert space.str_w(w_res) == "ABC"

    def test_to_str(self, space):
        w_res = space.execute('return "ABC".to_str')
        assert space.str_w(w_res) == "ABC"

    def test_length(self, space):
        w_res = space.execute("return 'ABC'.length")
        assert space.int_w(w_res) == 3
        w_res = space.execute("return 'ABC'.size")
        assert space.int_w(w_res) == 3

    def test_comparator_lt(self, space):
        w_res = space.execute("return 'a' <=> 'b'")
        assert space.int_w(w_res) == -1

    def test_comparator_eq(self, space):
        w_res = space.execute("return 'a' <=> 'a'")
        assert space.int_w(w_res) == 0

    def test_comparator_gt(self, space):
        w_res = space.execute("return 'b' <=> 'a'")
        assert space.int_w(w_res) == 1

    def test_comparator_to_type_without_to_str(self, space):
        w_res = space.execute("return 'b' <=> 1")
        assert w_res is space.w_nil

    def test_comparator_to_type_with_to_str(self, space):
        w_res = space.execute("""
        class A
          def to_str; 'A'; end
          def <=>(other); other <=> self.to_str; end
        end
        return 'A' <=> A.new
        """)
        assert space.int_w(w_res) == 0

    def test_hash(self, space):
        w_res = space.execute("""
        return ['abc'.hash, ('a' << 'b' << 'c').hash]
        """)
        h1, h2 = self.unwrap(space, w_res)
        assert h1 == h2

    def test_to_sym(self, space):
        w_res = space.execute("return 'abc'.to_sym")
        assert space.symbol_w(w_res) == "abc"

    def test_clear(self, space):
        w_res = space.execute("""
        a = 'hi'
        b = a
        a.clear
        return [a, b]
        """)
        assert self.unwrap(space, w_res) == ["", ""]

        w_res = space.execute("return ('a' << 'b').clear")
        assert self.unwrap(space, w_res) == ""

    def test_ljust(self, space):
        w_res = space.execute("""
        a = 'hi'
        return a, a.ljust(1)
        """)
        w_original, w_adjusted = space.listview(w_res)
        assert w_original is not w_adjusted
        assert space.str_w(w_adjusted) == space.str_w(w_original)

        w_res = space.execute("return 'a'.ljust(3)")
        assert space.str_w(w_res) == "a  "

        w_res = space.execute("return 'a'.ljust(3, 'l')")
        assert space.str_w(w_res) == "all"

        w_res = space.execute("return 'a'.ljust(5, '-_*')")
        assert space.str_w(w_res) == "a-_*-"

        with self.raises(space, "ArgumentError", "zero width padding"):
            space.execute("'hi'.ljust(10, '')")

    def test_split(self, space):
        w_res = space.execute("return 'a b c'.split")
        assert self.unwrap(space, w_res) == ["a", "b", "c"]
        w_res = space.execute("return 'a-b-c'.split('-')")
        assert self.unwrap(space, w_res) == ["a", "b", "c"]
        w_res = space.execute("return 'a-b-c'.split('-', 2)")
        assert self.unwrap(space, w_res) == ["a", "b-c"]
        w_res = space.execute("return 'a b c'.split(' ', -1)")
        assert self.unwrap(space, w_res) == ["a", "b", "c"]

    def test_dup(self, space):
        w_res = space.execute("""
        x = "abc"
        y = x.dup
        x << "def"
        return [x, y]
        """)
        x, y = self.unwrap(space, w_res)
        assert x == "abcdef"
        assert y == "abc"

    def test_to_i(self, space):
        w_res = space.execute('return "1234".to_i')
        assert space.int_w(w_res) == 1234
        w_res = space.execute('return "1010".to_i(2)')
        assert space.int_w(w_res) == 10
        w_res = space.execute('return "77".to_i(8)')
        assert space.int_w(w_res) == 63
        w_res = space.execute('return "AA".to_i(16)')
        assert space.int_w(w_res) == 170
