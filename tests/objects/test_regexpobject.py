from ..base import BaseTopazTest


class TestRegexpObject(BaseTopazTest):
    def test_source(self, space):
        w_res = space.execute("return /abc/.source")
        assert space.str_w(w_res) == "abc"

    def test_compile_regexps(self, space):
        space.execute("""
        /^/
        /(a|b)/
        /(ab|ac)/
        /(ms|min)/
        /$/
        /[^f]/
        /[a]+/
        /\\(/
        /[()#:]/
        /[^()#:]/
        /([^)]+)?/
        /cy|m/
        /[\\-]/
        /(?!a)/
        /(?=a)/
        /a{1}/
        /a{2,3}/
        /foo(?#comment)bar/
        /abc/i
        /(?<=\d)/
        /(?<foo>.*)/
        /A++/
        /.*?/
        /\\z/
        /[a-z]/
        /\\d+/
        /([a-z])|b/
        /[a-zA-z]|[a-z]/
        /(?<foo>a)\\g<foo>/
        /[^a-z]/
        /[a-z&&[^a-c]]/
        /[a&&[^b]]+/
        /\\G/
        /\\p{digit}/
        /\\P/
        /a{1,}/
        /a{,1}/
        /(?:abc)?/
        /(?:a|b)*/
        /.*/m
        /(.*|.+)/
        /(?<=b)/
        /\\A|\\z/
        """)

    def test_regexp_syntax_errors(self, space):
        with self.raises(space, "SyntaxError"):
            space.execute("/(?~)/")
        with self.raises(space, "RegexpError"):
            space.execute("""
            r = "(?~)"
            /#{r}/
            """)
        with self.raises(space, "RegexpError"):
            space.execute("""
            class Regexp
              def self.new(*args); /foo/; end
              def self.compile(*args); /foo/; end
            end
            r = "(?~)"
            /#{r}/
            """)

    def test_regexp_compile_errors(self, space):
        with self.raises(space, "RegexpError"):
            space.execute("Regexp.compile '?~'")
        with self.raises(space, "RegexpError"):
            space.execute("""
            class Regexp
              def self.new(*args); /foo/; end
            end
            Regexp.compile "(?~)"
            """)

    def test_regexp_new_errors(self, space):
        with self.raises(space, "RegexpError"):
            space.execute("Regexp.new '?~'")
        with self.raises(space, "RegexpError"):
            space.execute("""
            class Regexp
              def self.compile(*args); /foo/; end
            end
            Regexp.new "(?~)"
            """)

    def test_to_s(self, space):
        w_res = space.execute("return /a/.to_s")
        assert space.str_w(w_res) == "(?-mix:a)"

        w_res = space.execute("return /a/i.to_s")
        assert space.str_w(w_res) == "(?i-mx:a)"

    def test_match_operator(self, space):
        w_res = space.execute("""
        idx = /(l)(l)(o)(a)(b)(c)(h)(e)(l)/ =~ 'helloabchello'
        return idx, $1, $2, $3, $4, $5, $6, $7, $8, $9, $&, $+, $`, $'
        """)
        assert self.unwrap(space, w_res) == [2, "l", "l", "o", "a", "b", "c", "h", "e", "l", "lloabchel", "l", "he", "lo"]

    def test_match_method(self, space):
        w_res = space.execute("return /bc/.match('abc').begin(0)")
        assert space.int_w(w_res) == 1

    def test_match_begin(self, space):
        w_res = space.execute("return /a(bc(de))/.match(' abcde').begin(0)")
        assert space.int_w(w_res) == 1
        w_res = space.execute("return /a(bc(de))/.match(' abcde').begin(1)")
        assert space.int_w(w_res) == 2
        w_res = space.execute("return /a(bc(de))/.match(' abcde').begin(2)")
        assert space.int_w(w_res) == 4
        with self.raises(space, "IndexError", "index 3 out of matches"):
            space.execute("/a(bc(de))/.match(' abcde').begin(3)")

    def test_match_end(self, space):
        w_res = space.execute("return /a(bc(de))f/.match(' abcdef').end(0)")
        assert space.int_w(w_res) == 7
        w_res = space.execute("return /a(bc(de))f/.match(' abcdef').end(1)")
        assert space.int_w(w_res) == 6
        w_res = space.execute("return /a(bc(de))f/.match(' abcdef').end(2)")
        assert space.int_w(w_res) == 6
        with self.raises(space, "IndexError", "index 3 out of matches"):
            space.execute("/a(bc(de))/.match(' abcde').end(3)")

    def test_new_regexp(self, space):
        w_res = space.execute("return Regexp.new('..abc..') == Regexp.compile('..abc..')")
        assert w_res is space.w_true
        w_res = space.execute("return Regexp.new(/abc/).source")
        assert space.str_w(w_res) == "abc"

    def test_size(self, space):
        w_res = space.execute("""
        /(a)(b)(c)/ =~ "hey hey, abc, hey hey"
        return $~.size
        """)
        assert space.int_w(w_res) == 4

    def test_set_match_data_wrong_type(self, space):
        with self.raises(space, "TypeError"):
            space.execute("$~ = 12")
        space.execute("$~ = nil")

    def test_atomic_grouping(self, space):
        w_res = space.execute('return /"(?>.*)"/ =~ (\'"Quote"\')')
        assert w_res is space.w_nil

        w_res = space.execute('return /"(?>[A-Za-z]*)"/ =~ \'"Quote"\'')
        assert space.int_w(w_res) == 0

        w_res = space.execute('return /fooA++bar/.match("fooAAAbar").to_a')
        assert self.unwrap(space, w_res) == ["fooAAAbar"]

    def test_set_intersection(self, space):
        w_res = space.execute("return /[a-z&&[^a-c]]+/ =~ 'abcdef'")
        assert space.int_w(w_res) == 3

    def test_to_a(self, space):
        w_res = space.execute("""
        m = /(a)(b)(c)/.match('defabcdef')
        return m.to_a
        """)
        assert self.unwrap(space, w_res) == ["abc", "a", "b", "c"]

    def test_values_at(self, space):
        w_res = space.execute("""
        m = /(.)(.)(\d+)(\d)/.match("THX1138: The Movie")
        return m.values_at(0, 2, -2)
        """)
        assert self.unwrap(space, w_res) == ["HX1138", "X", "113"]

    def test_branch(self, space):
        w_res = space.execute("return /a|b/ =~ 'a'")
        assert space.int_w(w_res) == 0

    def test_dot(self, space):
        w_res = space.execute('return /./ =~ "\\n"')
        assert w_res is space.w_nil

        w_res = space.execute('return /./m =~ "\\n"')
        assert space.int_w(w_res) == 0

    def test_non_capturing_group(self, space):
        w_res = space.execute("return /(?:foo)(bar)/.match('foobar').to_a")
        assert self.unwrap(space, w_res) == ["foobar", "bar"]

    def test_optional_group(self, space):
        w_res = space.execute("return /(foo)?(bar)?/.match('foobar')[1]")
        assert self.unwrap(space, w_res) == "foo"
        w_res = space.execute("return /(foo)?(bar)?/.match('foobar')[2]")
        assert self.unwrap(space, w_res) == "bar"
        w_res = space.execute("return /(foo)?(bar)?/.match('foo')[2]")
        assert self.unwrap(space, w_res) is None

    def test_quantify_set(self, space):
        w_res = space.execute("return /([0-9]){3,5}?/ =~ 'ab12345'")
        assert space.int_w(w_res) == 2

    def test_quantify(self, space):
        w_res = space.execute("return /a{2,4}/.match('aaaaaa').to_a")
        assert self.unwrap(space, w_res) == ["aaaa"]

    def test_repeated_quantification(self, space):
        w_res = space.execute("return /(A{0,1}+)A/.match('AAA').to_a")
        assert self.unwrap(space, w_res) == ["AAA", "AA"]

    def test_casefoldp(self, space):
        w_res = space.execute("return /a/.casefold?")
        assert w_res is space.w_false
        w_res = space.execute("return /a/i.casefold?")
        assert w_res is space.w_true

    def test_eqeqeq(self, space):
        w_res = space.execute("return /abc/ === 'defabc'")
        assert w_res is space.w_true
        w_res = space.execute("return /abc/ === 'ddddddd'")
        assert w_res is space.w_false

    def test_escape(self, space):
        w_res = space.execute("""
        return Regexp.escape("y1_'\t\n\v\f\r \#$()*+-.?[\\\\]^{|}")
        """)
        assert space.str_w(w_res) == "y1_'\\t\\n\\v\\f\\r\\ \\#\\$\\(\\)\\*\\+\\-\\.\\?\\[\\\\\\]\\^\\{\\|\\}"

    def test_ignore_whitespace(self, space):
        w_res = space.execute("return /\d \d/x =~ '12'")
        assert space.int_w(w_res) == 0
