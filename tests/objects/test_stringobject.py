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
