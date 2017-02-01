from rpython.rlib.rbigint import rbigint

from ..base import BaseTopazTest
import pytest


class TestStringObject(BaseTopazTest):
    def test_new(self, space):
        w_res = space.execute("return String.new('abc')")
        assert space.str_w(w_res) == "abc"
        w_res = space.execute("return String.new")
        assert space.str_w(w_res) == ""

    def test_lshift(self, space):
        w_res = space.execute('return "abc" << "def" << "ghi"')
        assert space.str_w(w_res) == "abcdefghi"
        w_res = space.execute('return "abc".concat("def").concat("ghi")')
        assert space.str_w(w_res) == "abcdefghi"

    def test_plus(self, space):
        w_res = space.execute('return "abc" + "def" + "ghi"')
        assert space.str_w(w_res) == "abcdefghi"

    def test_mul(self, space):
        w_res = space.execute("return 'abc' * 2")
        assert space.str_w(w_res) == "abcabc"
        w_res = space.execute("return ('abc' << 'def') * 3")
        assert space.str_w(w_res) == "abcdefabcdefabcdef"

    def test_to_s(self, space):
        w_res = space.execute('return "ABC".to_s')
        assert space.str_w(w_res) == "ABC"

    def test_inspect(self, space):
        w_res = space.execute('return "abc".inspect')
        assert space.str_w(w_res) == '"abc"'

    def test_to_str(self, space):
        w_res = space.execute('return "ABC".to_str')
        assert space.str_w(w_res) == "ABC"

    def test_ord(self, space):
        w_res = space.execute('return "a".ord')
        assert space.int_w(w_res) == 97
        w_res = space.execute('return "asd".ord')
        assert space.int_w(w_res) == 97
        with self.raises(space, "ArgumentError", "empty string"):
            space.execute("''.ord")

    def test_length(self, space):
        w_res = space.execute("return 'ABC'.length")
        assert space.int_w(w_res) == 3
        w_res = space.execute("return 'ABC'.size")
        assert space.int_w(w_res) == 3

    def test_emptyp(self, space):
        w_res = space.execute("return ''.empty?")
        assert w_res is space.w_true
        w_res = space.execute("return 'a'.empty?")
        assert w_res is space.w_false

    def test_subscript_constant(self, space):
        w_res = space.execute("""
        a = "hello there"
        return [
          a[1],
          a[2, 3],
          a[2..3],
          a[-3, 2],
          a[7..-2],
          a[-4..-2],
          a[-2..-4],
          a[12..-1],
        ]
        """)
        assert self.unwrap(space, w_res) == ["e", "llo", "ll", "er", "her", "her", "", None]

    def test_subscript_mutable(self, space):
        w_res = space.execute("""
        a = "hello" << " " << "there"
        return [
          a[1],
          a[2, 3],
          a[2..3],
          a[-3, 2],
          a[7..-2],
          a[-4..-2],
          a[-2..-4],
          a[12..-1],
        ]
        """)
        assert self.unwrap(space, w_res) == ["e", "llo", "ll", "er", "her", "her", "", None]

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

    def test_eqlp(self, space):
        w_res = space.execute("return 'abc'.eql? 2")
        assert w_res is space.w_false
        w_res = space.execute("return 'abc'.eql? 'abc'")
        assert w_res is space.w_true

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

    def test_index(self, space):
        w_res = space.execute("return 'abc'.index 'a'")
        assert space.int_w(w_res) == 0
        w_res = space.execute("return 'abc'.index 'bc'")
        assert space.int_w(w_res) == 1
        w_res = space.execute("return 'aba'.index 'a', 1")
        assert space.int_w(w_res) == 2
        w_res = space.execute("return 'aba'.index 'c', 1")
        assert space.int_w(w_res) == -1
        w_res = space.execute("return 'aba'.index /ba/")
        assert space.int_w(w_res) == 1
        w_res = space.execute("return 'aba'.index /xyz/")
        assert space.int_w(w_res) == -1
        with self.raises(space, "TypeError", "type mismatch: Fixnum given"):
            space.execute("'a b c'.index 12")

    def test_rindex(self, space):
        w_res = space.execute('"hello".rindex("e")')
        assert space.int_w(w_res) == 1
        w_res = space.execute('"hello".rindex("l")')
        assert space.int_w(w_res) == 3
        w_res = space.execute('"hello".rindex("l", -3)')
        assert space.int_w(w_res) == 2
        w_res = space.execute('"hello".rindex("h", -5)')
        assert space.int_w(w_res) == 0
        w_res = space.execute('"hello".rindex(/[aeiou]/, -2)')
        assert space.int_w(w_res) == 1
        w_res = space.execute('"hello".rindex(/[aeiou]/, 0)')
        assert space.int_w(w_res) == 4
        w_res = space.execute('"hello".rindex(/[aeiou]/, 10)')
        assert space.int_w(w_res) == 4
        w_res = space.execute('"hello".rindex(/[aeiou]/, -1)')
        assert space.int_w(w_res) == 4
        w_res = space.execute('"hello".rindex(/[aeiou]/, -10)')
        assert w_res is space.w_nil
        w_res = space.execute('"hello".rindex(/[x]/)')
        assert w_res is space.w_nil
        w_res = space.execute('"hello".rindex("x")')
        assert w_res is space.w_nil
        with self.raises(space, "TypeError", "type mismatch: Fixnum given"):
            space.execute('"hello".rindex(123)')

    def test_split(self, space):
        w_res = space.execute("return 'a b c'.split")
        assert self.unwrap(space, w_res) == ["a", "b", "c"]
        w_res = space.execute("return 'a-b-c'.split('-')")
        assert self.unwrap(space, w_res) == ["a", "b", "c"]
        w_res = space.execute("return 'a-b-c'.split('-', 2)")
        assert self.unwrap(space, w_res) == ["a", "b-c"]
        w_res = space.execute("return 'a b c'.split(' ', -1)")
        assert self.unwrap(space, w_res) == ["a", "b", "c"]
        with self.raises(space, "TypeError", "wrong argument type Fixnum (expected Regexp)"):
            space.execute("'a b c'.split(12)")

    def test_split_regexp(self, space):
        w_res = space.execute("return \"now's  the time\".split(/ /)")
        assert self.unwrap(space, w_res) == ["now's", "", "the", "time"]
        w_res = space.execute('return "1, 2.34,56, 7".split(%r{,\s*})')
        assert self.unwrap(space, w_res) == ["1", "2.34", "56", "7"]
        w_res = space.execute('return "1, 2.34,56, 7".split(%r{,\s*}, 0)')
        assert self.unwrap(space, w_res) == ["1", "2.34", "56", "7"]
        w_res = space.execute('return "1, 2.34,56, 7".split(%r{,\s*}, -1)')
        assert self.unwrap(space, w_res) == ["1", "2.34", "56", "7", ""]
        w_res = space.execute('return "1, 2.34,56, 7".split(%r{,\s*}, -2)')
        assert self.unwrap(space, w_res) == ["1", "2.34", "56", "7", ""]
        w_res = space.execute('return "1, 2.34,56, 7".split(%r{,\s*}, 4)')
        assert self.unwrap(space, w_res) == ["1", "2.34", "56", "7"]
        w_res = space.execute('return "1, 2.34,56, 7".split(%r{,\s*}, 5)')
        assert self.unwrap(space, w_res) == ["1", "2.34", "56", "7", ""]
        w_res = space.execute('return "1, 2.34,56, 7".split(%r{,\s*}, 6)')
        assert self.unwrap(space, w_res) == ["1", "2.34", "56", "7", ""]
        w_res = space.execute('return "hello".split(//)')
        assert self.unwrap(space, w_res) == ["h", "e", "l", "l", "o"]
        w_res = space.execute('return "hello".split(//, 3)')
        assert self.unwrap(space, w_res) == ["h", "e", "llo"]
        w_res = space.execute('return "hello".split(/((.)(.))/, 3)')
        assert self.unwrap(space, w_res) == ["", "he", "h", "e", "", "ll", "l", "l", "o"]

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

    def test_dup_mutable(self, space):
        w_res = space.execute("return ('abc' << 'def').dup")
        assert self.unwrap(space, w_res) == 'abcdef'

    def test_to_i(self, space):
        w_res = space.execute('return "1234".to_i')
        assert space.int_w(w_res) == 1234
        w_res = space.execute('return "1010".to_i(2)')
        assert space.int_w(w_res) == 10
        w_res = space.execute('return "77".to_i(8)')
        assert space.int_w(w_res) == 63
        w_res = space.execute('return "AA".to_i(16)')
        assert space.int_w(w_res) == 170
        w_res = space.execute('return "12a".to_i')
        assert space.int_w(w_res) == 12
        w_res = space.execute('return "-a".to_i')
        assert space.int_w(w_res) == 0
        w_res = space.execute('return "".to_i')
        assert space.int_w(w_res) == 0
        w_res = space.execute('return "-12fdsa".to_i')
        assert space.int_w(w_res) == -12
        w_res = space.execute("return '1_2_3'.to_i")
        assert space.int_w(w_res) == 123
        w_res = space.execute("return '_1_2_3'.to_i")
        assert space.int_w(w_res) == 0
        w_res = space.execute("return '   123'.to_i")
        assert space.int_w(w_res) == 123

        w_res = space.execute("return '234124123123123121231231'.to_i")
        assert space.bigint_w(w_res) == rbigint.fromlong(234124123123123121231231)

        with self.raises(space, "ArgumentError"):
            space.execute('"".to_i(1)')
        with self.raises(space, "ArgumentError"):
            space.execute('"".to_i(37)')

    def test_to_f(self, space):
        w_res = space.execute('return "123.45".to_f')
        assert space.float_w(w_res) == 123.45

        w_res = space.execute('return "45.67 degrees".to_f')
        assert space.float_w(w_res) == 45.67

        w_res = space.execute('return "thx1138".to_f')
        assert space.float_w(w_res) == 0.0

        w_res = space.execute('return "123.45e1".to_f')
        assert space.float_w(w_res) == 1234.5

        w_res = space.execute('return "  123.45e1".to_f')
        assert space.float_w(w_res) == 1234.5

    def test_swapcase(self, space):
        w_res = space.execute("""
        a = "AbC123aBc"
        a.swapcase!
        return a
        """)
        assert self.unwrap(space, w_res) == "aBc123AbC"

        w_res = space.execute("return 'AbC123aBc'.swapcase")
        assert self.unwrap(space, w_res) == "aBc123AbC"

        w_res = space.execute("return '123'.swapcase!")
        assert w_res is space.w_nil

    def test_upcase(self, space):
        w_res = space.execute("""
        a = "AbC123aBc"
        a.upcase!
        return a
        """)
        assert self.unwrap(space, w_res) == "ABC123ABC"

        w_res = space.execute("return 'AbC123aBc'.upcase")
        assert self.unwrap(space, w_res) == "ABC123ABC"

        w_res = space.execute("return '123'.upcase!")
        assert w_res is space.w_nil

    def test_downcase(self, space):
        w_res = space.execute("""
        a = "AbC123aBc"
        a.downcase!
        return a
        """)
        assert self.unwrap(space, w_res) == "abc123abc"

        w_res = space.execute("return 'AbC123aBc'.downcase")
        assert self.unwrap(space, w_res) == "abc123abc"

        w_res = space.execute("return '123'.downcase!")
        assert w_res is space.w_nil

    def test_capitalize(self, space):
        w_res = space.execute("""
        a = "123ABC"
        a.capitalize!
        return a
        """)
        assert self.unwrap(space, w_res) == "123abc"

        w_res = space.execute("return 'hello'.capitalize")
        assert self.unwrap(space, w_res) == "Hello"
        w_res = space.execute("return 'HELLO'.capitalize")
        assert self.unwrap(space, w_res) == "Hello"
        w_res = space.execute("return '123'.capitalize!")
        assert w_res is space.w_nil

    def test_tr(self, space):
        w_res = space.execute("return 'hello'.tr('el', 'ip')")
        assert space.str_w(w_res) == "hippo"
        w_res = space.execute("return 'hello'.tr('aeiou', '*')")
        assert space.str_w(w_res) == "h*ll*"
        w_res = space.execute("return 'hello'.tr('a-y', 'b-z')")
        assert space.str_w(w_res) == "ifmmp"
        w_res = space.execute("return 'hello'.tr('^aieou', '*')")
        assert space.str_w(w_res) == "*e**o"
        w_res = space.execute("return 'hello'.tr!('','').nil?")
        assert self.unwrap(space, w_res) is True
        w_res = space.execute("""
        s = 'hello'
        s.tr!('e', 'a')
        return s
        """)
        assert space.str_w(w_res) == "hallo"
        w_res = space.execute("return 'x'.tr('x', '-')")
        assert space.str_w(w_res) == "-"

    def test_tr_s(self, space):
        w_res = space.execute("return 'hello'.tr_s('l', 'r')")
        assert space.str_w(w_res) == "hero"
        w_res = space.execute("return 'hello'.tr_s('el', '*')")
        assert space.str_w(w_res) == "h*o"
        w_res = space.execute("return 'hello'.tr_s('el', 'hx')")
        assert space.str_w(w_res) == "hhxo"
        w_res = space.execute("""
        s = 'hello'
        s.tr_s!('el', 'hx')
        return s
        """)
        assert space.str_w(w_res) == "hhxo"
        w_res = space.execute("return 'hello'.tr_s!('','').nil?")
        assert self.unwrap(space, w_res) is True

    def test_match_operator(self, space):
        w_res = space.execute("return 'abc' =~ 1")
        assert w_res is space.w_nil
        w_res = space.execute("return 'abc' =~ /abc/")
        assert space.int_w(w_res) == 0
        w_res = space.execute("""
        '' =~ /()/
        return $1
        """)
        assert space.str_w(w_res) == ""

    def test_match_method(self, space):
        w_res = space.execute("return 'abc'.match('bc').begin 0")
        assert space.int_w(w_res) == 1

    def test_getbyte(self, space):
        w_res = space.execute("return 'abc'.getbyte 0")
        assert space.int_w(w_res) == 97
        w_res = space.execute("return 'abc'.getbyte 2")
        assert space.int_w(w_res) == 99
        w_res = space.execute("return 'abc'.getbyte 3")
        assert w_res is space.w_nil
        w_res = space.execute("return 'abc'.getbyte -1")
        assert space.int_w(w_res) == 99
        w_res = space.execute("return 'abc'.getbyte -3")
        assert space.int_w(w_res) == 97
        w_res = space.execute("return 'abc'.getbyte -4")
        assert w_res is space.w_nil

    def test_chomp(self, space):
        assert space.str_w(space.execute('return "hello".chomp')) == "hello"
        assert space.str_w(space.execute('return "hello\\n".chomp')) == "hello"
        assert space.str_w(space.execute('return "hello\\r\\n".chomp')) == "hello"
        assert space.str_w(space.execute('return "hello\\n\\r".chomp')) == "hello"
        assert space.str_w(space.execute('return "hello\\r".chomp')) == "hello"
        assert space.str_w(space.execute('return "hello\\r".chomp("")')) == "hello\r"
        assert space.str_w(space.execute('return "hello \\n there".chomp')) == "hello \n there"
        assert space.str_w(space.execute('return "hello".chomp("llo")')) == "he"
        w_res = space.execute('return "hello".chomp!')
        assert w_res is space.w_nil
        w_res = space.execute('return "".chomp!')
        assert w_res is space.w_nil
        w_res = space.execute('return "abc".chomp!(nil)')
        assert w_res is space.w_nil
        w_res = space.execute('return "abc\\r".chomp!("")')
        assert w_res is space.w_nil

    def test_chop(self, space):
        assert space.str_w(space.execute('return "string\\r\\n".chop')) == "string"
        assert space.str_w(space.execute('return "string\\n\\r".chop')) == "string\n"
        assert space.str_w(space.execute('return "string\\n".chop')) == "string"
        assert space.str_w(space.execute('return "string".chop')) == "strin"
        assert space.str_w(space.execute('return "x".chop.chop')) == ""
        assert space.str_w(space.execute('return "string".chop!')) == "strin"
        w_res = space.execute("return ''.chop!")
        assert w_res is space.w_nil

    def test_reverse(self, space):
        assert space.str_w(space.execute('return "stressed".reverse')) == "desserts"
        w_res = space.execute("""
        a = "stressed"
        a.reverse!
        return a, a.reverse
        """)
        assert self.unwrap(space, w_res) == ["desserts", "stressed"]

    def test_includep(self, space):
        assert space.execute("return 'abc'.include? 'ab'") is space.w_true
        assert space.execute("return 'abc'.include? 'bc'") is space.w_true
        assert space.execute("return 'abc'.include? 'cd'") is space.w_false

    def test_gsub(self, space):
        w_res = space.execute("""
        return 'hello hello'.gsub("he", "ha")
        """)
        assert space.str_w(w_res) == "hallo hallo"
        w_res = space.execute("""
        return 'hello'.gsub(/(.)/, "ha")
        """)
        assert space.str_w(w_res) == "hahahahaha"
        w_res = space.execute("""
        return 'hello'.gsub(/(.)/, "ha\\\\1ho")
        """)
        assert space.str_w(w_res) == "hahhohaehohalhohalhohaoho"
        w_res = space.execute("""
        return 'hello'.gsub(/(.)/) { |e| e + "1" }
        """)
        assert space.str_w(w_res) == "h1e1l1l1o1"
        w_res = space.execute("""
        return 'hello'.gsub('e') { |e| e + "1" }
        """)
        assert space.str_w(w_res) == "he1llo"
        w_res = space.execute("""
        return 'hello'.gsub(/[eo]/, 'e' => 3, 'o' => '*')
        """)
        assert space.str_w(w_res) == "h3ll*"
        w_res = space.execute("""
        return 'hello'.gsub("e", 'e' => 3, 'o' => '*')
        """)
        assert space.str_w(w_res) == "h3llo"
        w_res = space.execute("""
        replacements = [1, 2]
        return 'helloo'.gsub("l", Hash.new { |h, k| replacements.pop() })
        """)
        assert space.str_w(w_res) == "he21oo"

    def test_sub(self, space):
        w_res = space.execute("""
        return 'hello hello'.sub("he", "ha")
        """)
        assert space.str_w(w_res) == "hallo hello"
        w_res = space.execute("""
        return 'hello'.sub(/(.)/, "ha")
        """)
        assert space.str_w(w_res) == "haello"
        w_res = space.execute("""
        return 'hello'.sub(/(.)/, "ha\\\\1ho")
        """)
        assert space.str_w(w_res) == "hahhoello"
        w_res = space.execute("""
        return 'hello'.sub(/(.)/) { |e| e + "1" }
        """)
        assert space.str_w(w_res) == "h1ello"
        w_res = space.execute("""
        return 'hello'.sub('l') { |e| e + "1" }
        """)
        assert space.str_w(w_res) == "hel1lo"
        w_res = space.execute("""
        return 'hello'.sub(/[eo]/, 'e' => 3, 'o' => '*')
        """)
        assert space.str_w(w_res) == "h3llo"
        w_res = space.execute("""
        return 'hello'.sub("e", 'e' => 3, 'o' => '*')
        """)
        assert space.str_w(w_res) == "h3llo"
        w_res = space.execute("""
        replacements = [1, 2]
        return 'helloo'.sub("l", Hash.new { |h, k| replacements.pop() })
        """)
        assert space.str_w(w_res) == "he2loo"
        with self.raises(space, "ArgumentError"):
            space.execute("'string'.sub(/regex/)")

    def test_succ(self, space):
        w_res = space.execute('return "abcd".succ')
        assert space.str_w(w_res) == "abce"
        w_res = space.execute('return "THX1138".succ')
        assert space.str_w(w_res) == "THX1139"
        w_res = space.execute('return "<<koala>>".succ')
        assert space.str_w(w_res) == "<<koalb>>"
        w_res = space.execute('return "ZZZ9999".succ')
        assert space.str_w(w_res) == "AAAA0000"
        w_res = space.execute('return "***".succ')
        assert space.str_w(w_res) == "**+"

    def test_slice(self, space):
        w_res = space.execute('return "this is a string".slice(2)')
        assert space.str_w(w_res) == "i"
        w_res = space.execute('return "hello".slice(2, 3)')
        assert space.str_w(w_res) == "llo"

    def test_slice_i(self, space):
        w_res = space.execute('return "this is a string".slice!(2)')
        assert space.str_w(w_res) == "i"
        w_res = space.execute('return "this is a string".slice!(2, 5)')
        assert space.str_w(w_res) == "is is"
        w_res = space.execute("""
        string = "this is a string"
        string.slice!(2)
        string.slice!(3..6)
        return string
        """)
        assert space.str_w(w_res) == "thsa string"

    @pytest.mark.xfail
    def test_byte_representation(self, space):
        w_res = space.execute('return "\x00".length')
        assert space.int_w(w_res) == 1

        w_res = space.execute("return '\x00'.length")
        assert space.int_w(w_res) == 4

        w_res = space.execute('return "\x04\bi\x00".length')
        assert space.int_w(w_res) == 4

        w_res = space.execute("return '\x04\bi\x00'.length")
        assert space.int_w(w_res) == 11


class TestStringMod(object):
    def test_s(self, space):
        w_res = space.execute("return '1 %s 1' % 'abc'")
        assert space.str_w(w_res) == "1 abc 1"

    def test_f(self, space):
        w_res = space.execute("return ' %f ' % 1.23")
        assert space.str_w(w_res) == " 1.230000 "

    def test_f_width(self, space):
        w_res = space.execute("return '%04f' % 1.23")
        assert space.str_w(w_res) == "1.230000"

    def test_d(self, space):
        w_res = space.execute("return ' %d ' % 12")
        assert space.str_w(w_res) == " 12 "

    def test_d_width(self, space):
        w_res = space.execute("return ' %05d' % 12")
        assert space.str_w(w_res) == " 00012"
        w_res = space.execute("return ' %01d' % 12")
        assert space.str_w(w_res) == " 12"

    def test_array_param(self, space):
        w_res = space.execute("return '%d-%s' % [12, 'happy']")
        assert space.str_w(w_res) == "12-happy"
        w_res = space.execute("return '1%02d%02d%02d%04d' % [1, 2, 3, 4]")
        assert space.str_w(w_res) == "10102030004"
