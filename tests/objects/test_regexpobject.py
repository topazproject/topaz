from ..base import BaseRuPyPyTest


class TestRegexp(BaseRuPyPyTest):
    def test_source(self, space):
        w_res = space.execute("return /abc/.source")
        assert space.str_w(w_res) == "abc"

    def test_match(self, space):
        w_res = space.execute("""
        idx = /(l)(l)(o)(a)(b)(c)(h)(e)(l)/ =~ 'helloabchello'
        return idx, $1, $2, $3, $4, $5, $6, $7, $8, $9, $&, $+, $`, $'
        """)
        assert self.unwrap(space, w_res) == [2] + [s for s in "lloabchel"] + ["lloabchel", "l", "he", "lo"]

    def test_match_resets_globals(self, space):
        w_res = space.execute("""
        idx = /(l)(l)(o)(a)(b)(c)(h)(e)(l)/ =~ 'helloabchello'
        /nomatch/ =~ "this"
        return $1, $2, $3, $4, $5, $6, $7, $8, $9, $&, $+, $`, $'
        """)
        assert self.unwrap(space, w_res) == [None] * 13

    def test_match_ignore_case_global(self, space):
        w_res = space.execute("""
        idx1 = /abc/ =~ "ABC"
        $= = true
        idx2 = /abc/ =~ "ABC"
        return idx1, idx2
        """)
        assert self.unwrap(space, w_res) == [None, 0]
