from ..base import BaseRuPyPyTest


class TestRegexpObject(BaseRuPyPyTest):
    def test_source(self, space):
        w_res = space.execute("return /abc/.source")
        assert space.str_w(w_res) == "abc"

    def test_match_operator(self, space):
        w_res = space.execute("""
        idx = /(l)(l)(o)(a)(b)(c)(h)(e)(l)/ =~ 'helloabchello'
        return idx, $1, $2, $3, $4, $5, $6, $7, $8, $9, $&, $+, $`, $'
        """)
        assert self.unwrap(space, w_res) == [2, "l", "l", "o", "a", "b", "c", "h", "e", "l", "lloabchel", "l", "he", "lo"]

    def test_new_regexp(self, space):
        w_res = space.execute("return Regexp.new('..abc..') == Regexp.compile('..abc..')")
        assert w_res is space.w_true
