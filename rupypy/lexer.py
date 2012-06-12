import string

from pypy.rlib.parsing.lexer import Token, SourcePos


class LexerError(Exception):
    def __init__(self, pos):
        self.pos = pos


class Keyword(object):
    def __init__(self, normal_token, inline_token, state):
        self.normal_token = normal_token
        self.inline_token = inline_token
        self.state = state


class BaseLexer(object):
    EOF = chr(0)

    EXPR_BEG = 0
    EXPR_END = 1
    EXPR_ARG = 2
    EXPR_CMDARG = 3
    EXPR_ENDARG = 4
    EXPR_MID = 5
    EXPR_FNAME = 6
    EXPR_DOT = 7
    EXPR_CLASS = 8
    EXPR_VALUE = 9
    EXPR_ENDFN = 10

    keywords = {
        "return": Keyword("RETURN", "RETURN", EXPR_MID),
        "yield": Keyword("YIELD", "YIELD", EXPR_ARG),
        "if": Keyword("IF", "IF_INLINE", EXPR_BEG),
        "unless": Keyword("UNLESS", "UNLESS_INLINE", EXPR_BEG),
        "then": Keyword("THEN", "THEN", EXPR_BEG),
        "elsif": Keyword("ELSIF", "ELSIF", EXPR_BEG),
        "else": Keyword("ELSE", "ELSE", EXPR_BEG),
        "while": Keyword("WHILE", "WHILE_INLINE", EXPR_BEG),
        "until": Keyword("UNTIL", "UNTIL_INLINE", EXPR_BEG),
        "do": Keyword("DO", "DO", EXPR_BEG),
        "begin": Keyword("BEGIN", "BEGIN", EXPR_BEG),
        "rescue": Keyword("RESCUE", "RESCUE_INLINE", EXPR_MID),
        "ensure": Keyword("ENSURE", "ENSURE", EXPR_BEG),
        "def": Keyword("DEF", "DEF", EXPR_FNAME),
        "class": Keyword("CLASS", "CLASS", EXPR_CLASS),
        "module": Keyword("MODULE", "MODULE", EXPR_BEG),
        "case": Keyword("CASE", "CASE", EXPR_BEG),
        "when": Keyword("WHEN", "WHEN", EXPR_BEG),
        "end": Keyword("END", "END", EXPR_END),
        "and": Keyword("AND_LITERAL", "AND_LITERAL", EXPR_BEG),
        "or": Keyword("OR_LITERAL", "OR_LITERAL", EXPR_BEG),
        "not": Keyword("NOT_LITERAL", "NOT_LITERAL", EXPR_BEG),
    }

    def __init__(self):
        self.tokens = []
        self.current_value = []

    def peek(self):
        ch = self.read()
        self.unread()
        return ch

    def add(self, ch):
        self.current_value.append(ch)

    def clear(self):
        del self.current_value[:]

    def current_pos(self):
        return SourcePos(self.get_idx(), self.get_lineno(), self.get_columno())

    def emit(self, token):
        value = "".join(self.current_value)
        self.clear()
        self.tokens.append(Token(token, value, self.current_pos()))


class Lexer(BaseLexer):
    def __init__(self, source):
        BaseLexer.__init__(self)
        self.source = source
        self.idx = 0
        self.lineno = 1
        self.columno = 1
        self.state = self.EXPR_BEG

    def tokenize(self):
        space_seen = False
        while True:
            ch = self.read()
            if ch == self.EOF:
                self.emit("EOF")
                return self.tokens
            if ch == " ":
                space_seen = True
                continue
            elif ch == "#":
                self.comment(ch)
            elif ch == "\n":
                space_seen = True
                if self.state != self.EXPR_BEG:
                    self.add(ch)
                    self.emit("LINE_END")
                self.lineno += 1
                self.columno = 1
                self.state = self.EXPR_BEG
            elif ch == "*":
                self.star(ch, space_seen)
            elif ch == "!":
                self.exclamation(ch)
            elif ch == "=":
                self.equal(ch)
            elif ch == "<":
                self.less_than(ch)
            elif ch == ">":
                self.greater_than(ch)
            elif ch == '"':
                tokens = StringLexer(self, '"', '"').tokenize()
                self.tokens.extend(tokens)
                self.state = self.EXPR_END
            elif ch == "'":
                self.single_quote(ch)
            elif ch == "?":
                self.question_mark(ch)
            elif ch == "&":
                self.ampersand(ch)
            elif ch == "|":
                self.pipe(ch)
            elif ch == "+":
                self.plus(ch)
            elif ch == "-":
                self.minus(ch, space_seen)
            elif ch == ".":
                self.dot(ch)
            elif ch.isdigit():
                self.number(ch)
            elif ch == ")":
                self.add(ch)
                self.state = self.EXPR_ENDFN
                self.emit("RPAREN")
            elif ch == "]":
                self.add(ch)
                self.state = self.EXPR_ENDARG
                self.emit("RBRACKET")
            elif ch == "}":
                self.add(ch)
                self.emit("RBRACE")
                self.state = self.EXPR_ENDFN
            elif ch == ":":
                self.colon(ch)
            elif ch == "/":
                self.slash(ch, space_seen)
            elif ch == "^":
                self.add(ch)
                self.set_expression_state()
                self.emit("CARET")
            elif ch == ";":
                self.add(ch)
                self.state = self.EXPR_BEG
                self.emit("LINE_END")
            elif ch == ",":
                self.add(ch)
                self.state = self.EXPR_BEG
                self.emit("COMMA")
            elif ch == "~":
                self.add(ch)
                self.state = self.EXPR_BEG
                self.emit("TILDE")
            elif ch == "(":
                self.add(ch)
                self.state = self.EXPR_BEG
                self.emit("LPAREN")
            elif ch == "[":
                self.left_bracket(ch, space_seen)
            elif ch == "{":
                self.add(ch)
                self.emit("LBRACE")
                self.state = self.EXPR_BEG
            elif ch == "%":
                self.percent(ch, space_seen)
            elif ch == "$":
                self.dollar(ch)
            elif ch == "@":
                self.at(ch)
            elif ch == "`":
                self.backtick(ch)
            else:
                self.identifier(ch)
            space_seen = False

    def read(self):
        try:
            ch = self.source[self.idx]
        except IndexError:
            ch = self.EOF
        self.idx += 1
        self.columno += 1
        return ch

    def unread(self):
        self.idx -= 1
        self.columno -= 1

    def get_idx(self):
        return self.idx

    def get_lineno(self):
        return self.lineno

    def get_columno(self):
        return self.columno

    def is_beg(self):
        return self.state in [self.EXPR_BEG, self.EXPR_MID, self.EXPR_CLASS, self.EXPR_VALUE]

    def is_arg(self):
        return self.state in [self.EXPR_ARG, self.EXPR_CMDARG]

    def is_end(self):
        return self.state in [self.EXPR_END, self.EXPR_ENDARG, self.EXPR_ENDFN]

    def set_expression_state(self):
        if self.state in [self.EXPR_FNAME, self.EXPR_DOT]:
            self.state = self.EXPR_ARG
        else:
            self.state = self.EXPR_BEG

    def emit_identifier(self):
        value = "".join(self.current_value)
        state = self.state
        if value in self.keywords and self.state not in [self.EXPR_DOT, self.EXPR_FNAME]:
            keyword = self.keywords[value]
            self.state = keyword.state

            if state in [self.EXPR_BEG, self.EXPR_VALUE]:
                self.emit(keyword.normal_token)
            else:
                self.emit(keyword.inline_token)
                if keyword.inline_token != keyword.normal_token:
                    self.state = self.EXPR_BEG
        else:
            self.emit("IDENTIFIER")
            if self.is_beg() or self.state == self.EXPR_DOT or self.is_arg():
                self.state = self.EXPR_ARG
            elif self.state == self.EXPR_ENDFN:
                self.state = self.EXPR_ENDFN
            else:
                self.state = self.EXPR_END

    def comment(self, ch):
        while True:
            ch = self.read()
            if ch == self.EOF or ch == "\n":
                self.unread()
                break

    def identifier(self, ch):
        self.add(ch)
        while True:
            ch = self.read()
            if ch == self.EOF:
                self.emit_identifier()
                self.unread()
                break
            if ch in "!?" or (ch == "=" and self.state == self.EXPR_FNAME):
                self.add(ch)
                self.emit_identifier()
                break
            elif ch.isalnum() or ch == "_":
                self.add(ch)
            else:
                state = self.state
                self.emit_identifier()
                if state == self.EXPR_FNAME and ch == ".":
                    self.add(ch)
                    self.emit("DOT")
                    self.state = self.EXPR_FNAME
                else:
                    self.unread()
                break

    def number(self, ch):
        self.state = self.EXPR_END
        self.add(ch)
        first_zero = ch == "0"
        is_hex = False
        while True:
            ch = self.read()
            if ch == self.EOF:
                self.emit("NUMBER")
                self.unread()
                break
            if first_zero and ch.upper() in "XBDO":
                if ch.upper() != "D":
                    self.add(ch.upper())
                is_hex = ch.upper() == "X"
            elif ch == ".":
                if not self.peek().isdigit():
                    self.emit("NUMBER")
                    self.unread()
                    break
                self.add(ch)
            elif ch.isdigit() or (is_hex and ch.upper() in "ABCDEF"):
                self.add(ch)
            elif ch == "_":
                if not self.peek().isdigit():
                    self.error()
            elif ch.upper() == "E":
                self.add(ch.upper())
            else:
                self.emit("NUMBER")
                self.unread()
                break
            first_zero = False

    def single_quote(self, ch):
        self.state = self.EXPR_END
        while True:
            ch = self.read()
            if ch == self.EOF:
                self.unread()
                break
            elif ch == "'":
                self.emit("SSTRING")
                break
            else:
                self.add(ch)

    def regexp(self, begin, end):
        self.emit("REGEXP_BEGIN")
        tokens = StringLexer(self, begin, end, interpolate=True).tokenize()
        self.tokens.extend(tokens)
        self.emit("REGEXP_END")
        self.state = self.EXPR_END

    def dollar(self, ch):
        self.add(ch)
        self.state = self.EXPR_END
        ch = self.read()
        if ch in "$>:?\\":
            self.add(ch)
            self.emit("GLOBAL")
        else:
            self.unread()
            while True:
                ch = self.read()
                if ch.isalnum() or ch == "_":
                    self.add(ch)
                else:
                    self.unread()
                    self.emit("GLOBAL")
                    break

    def at(self, ch):
        self.add(ch)
        ch = self.read()
        if ch == "@":
            self.add(ch)
            token = "CLASS_VAR"
        else:
            self.unread()
            token = "INSTANCE_VAR"
        self.state = self.EXPR_END
        while True:
            ch = self.read()
            if ch.isalnum() or ch == "_":
                self.add(ch)
            else:
                self.unread()
                self.emit(token)
                break

    def plus(self, ch):
        self.add(ch)
        ch2 = self.read()
        if ch2 == "=":
            self.add(ch2)
            self.emit("PLUS_EQUAL")
        else:
            self.unread()
            self.state = self.EXPR_BEG
            self.emit("PLUS")

    def minus(self, ch, space_seen):
        self.add(ch)
        ch2 = self.read()
        if ch2 == "=":
            self.add(ch2)
            self.state = self.EXPR_BEG
            self.emit("MINUS_EQUAL")
        elif self.is_beg() or (self.is_arg() and space_seen and not ch2.isspace()):
            self.state = self.EXPR_BEG
            if ch2.isdigit():
                self.number(ch2)
            else:
                self.unread()
                self.emit("UNARY_MINUS")
        else:
            self.unread()
            self.state = self.EXPR_BEG
            self.emit("MINUS")

    def star(self, ch, space_seen):
        self.add(ch)
        ch2 = self.read()
        if ch2 == "=":
            self.add(ch2)
            self.state = self.EXPR_BEG
            self.emit("MUL_EQUAL")
        elif ch2 == "*":
            self.add(ch2)
            self.set_expression_state()
            self.emit("POW")
        else:
            self.unread()
            if self.is_beg() or (self.is_arg() and space_seen and not ch2.isspace()):
                self.emit("UNARY_STAR")
            else:
                self.emit("MUL")
            self.set_expression_state()

    def slash(self, ch, space_seen):
        if self.is_beg():
            self.regexp("/", "/")
        else:
            ch2 = self.read()
            if ch2 == "=":
                self.add(ch)
                self.add(ch2)
                self.emit("DIV_EQUAL")
                self.state = self.EXPR_BEG
            else:
                self.unread()
                if self.is_arg() and space_seen and not ch2.isspace():
                    self.regexp("/", "/")
                else:
                    self.add(ch)
                    self.set_expression_state()
                    self.emit("DIV")

    def pipe(self, ch):
        self.add(ch)
        ch2 = self.read()
        if ch2 == "|":
            self.add(ch2)
            self.state = self.EXPR_BEG
            ch3 = self.read()
            if ch3 == "=":
                self.add(ch3)
                self.emit("OR_EQUAL")
            else:
                self.unread()
                self.emit("OR")
        else:
            self.unread()
            self.set_expression_state()
            self.emit("PIPE")

    def ampersand(self, ch):
        self.add(ch)
        ch2 = self.read()
        self.set_expression_state()
        if ch2 == "&":
            self.add(ch2)
            ch3 = self.read()
            if ch3 == "=":
                self.add(ch3)
                self.emit("AND_EQUAL")
            else:
                self.unread()
                self.emit("AND")
        else:
            self.unread()
            self.emit("AMP")

    def equal(self, ch):
        self.add(ch)
        self.set_expression_state()
        ch2 = self.read()
        if ch2 == "=":
            self.add(ch2)
            ch3 = self.read()
            if ch3 == "=":
                self.add(ch3)
                self.emit("EQEQEQ")
            else:
                self.unread()
                self.emit("EQEQ")
        elif ch2 == "~":
            self.add(ch2)
            self.emit("EQUAL_TILDE")
        elif ch2 == ">":
            self.add(ch2)
            self.emit("ARROW")
        else:
            self.unread()
            self.emit("EQ")

    def less_than(self, ch):
        self.add(ch)
        self.set_expression_state()
        ch2 = self.read()
        if ch2 == "=":
            self.add(ch2)
            ch3 = self.read()
            if ch3 == ">":
                self.add(ch3)
                self.emit("LEGT")
            else:
                self.unread()
                self.emit("LE")
        elif ch2 == "<":
            self.add(ch2)
            self.emit("LSHIFT")
        else:
            self.unread()
            self.emit("LT")

    def greater_than(self, ch):
        self.add(ch)
        self.set_expression_state()
        ch2 = self.read()
        if ch2 == "=":
            self.add(ch2)
            self.emit("GE")
        elif ch2 == ">":
            self.add(ch2)
            self.emit("RSHIFT")
        else:
            self.unread()
            self.emit("GT")

    def dot(self, ch):
        self.add(ch)
        self.state = self.EXPR_BEG
        ch2 = self.read()
        if ch2 == ".":
            self.add(ch2)
            ch3 = self.read()
            if ch3 == ".":
                self.add(ch3)
                self.emit("DOTDOTDOT")
            else:
                self.unread()
                self.emit("DOTDOT")
        else:
            self.unread()
            self.state = self.EXPR_DOT
            self.emit("DOT")

    def exclamation(self, ch):
        self.add(ch)
        self.state = self.EXPR_BEG

        ch2 = self.read()
        if ch2 == "=":
            self.add(ch2)
            self.emit("NE")
        elif ch2 == "~":
            self.add(ch2)
            self.emit("EXCLAMATION_TILDE")
        else:
            self.unread()
            self.emit("EXCLAMATION")

    def question_mark(self, ch):
        if self.is_end():
            self.add(ch)
            self.state = self.EXPR_VALUE
            self.emit("QUESTION")
        else:
            ch2 = self.read()
            if ch2.isspace():
                self.unread()
                self.add(ch)
                self.state = self.EXPR_VALUE
                self.emit("QUESTION")
            else:
                if ch2 == "\\":
                    self.add(self.read_escape())
                else:
                    self.add(ch2)
                self.emit("SSTRING")
                self.state = self.EXPR_END

    def read_escape(self):
        c = self.read()
        if c == self.EOF:
            self.error()
        elif c == "\\":
            return "\\"
        elif c == "n":
            return "\n"
        elif c == "t":
            return "\t"
        elif c == "r":
            return "\r"
        elif c == "f":
            return "\f"
        elif c == "v":
            return "\v"
        elif c == "a":
            return "\a"
        elif c == "b":
            return "\b"
        elif c == "e":
            return "\x1b"
        elif c == "s":
            return " "
        elif c == "u":
            raise NotImplementedError("UTF-8 escape not implemented")
        elif c in "x0":
            buf = ""
            for i in xrange(2):
                ch2 = self.read()
                if ch2.isalnum():
                    if c == "x" and not ch2 in string.hexdigits:
                        self.error()
                    if c == "0" and not ch2 in string.octdigits:
                        self.error()
                    buf += ch2
                else:
                    break
            if c == "x":
                return chr(int(buf, 16))
            elif c == "0":
                return chr(int(buf, 8))
        elif c == "M":
            if self.read() != "-":
                self.error()
            c = self.read()
            if c == "\\":
                return chr(ord(self.read_escape()) & 0x80)
            elif c == self.EOF:
                self.error()
            else:
                return chr(ord(c) & 0xff | 0x80)
        elif c == "C" or c == "c":
            if c == "C" and self.read() != "-":
                self.error()
            c = self.read()
            if c == "?":
                return '\177'
            elif c == self.EOF:
                self.error()
            else:
                if c == "\\":
                    c = self.read_escape()
                return chr(ord(c) & 0x9f)
        else:
            return c

    def colon(self, ch):
        ch2 = self.read()

        if ch2 == ":":
            self.add(ch)
            self.add(ch2)
            self.state = self.EXPR_DOT
            self.emit("COLONCOLON")
        elif self.is_end() or ch2.isspace():
            self.unread()
            self.add(ch)
            self.state = self.EXPR_BEG
            self.emit("COLON")
        else:
            self.unread()
            self.state = self.EXPR_FNAME
            self.emit("SYMBOL_BEGIN")

    def left_bracket(self, ch, space_seen):
        self.add(ch)
        if self.is_beg() or (self.is_arg() and space_seen):
            self.emit("LBRACKET")
        else:
            self.emit("LSUBSCRIPT")
        self.state = self.EXPR_BEG

    def backtick(self, ch):
        if self.state == self.EXPR_FNAME:
            self.add(ch)
            self.emit_identifier()
        elif self.state == self.EXPR_DOT:
            raise NotImplementedError("`")
        else:
            self.shellout("`", "`")

    def shellout(self, begin, end):
        self.emit("SHELL_BEGIN")
        tokens = StringLexer(self, begin, end, interpolate=True).tokenize()
        self.tokens.extend(tokens)
        self.emit("SHELL_END")
        self.state = self.EXPR_END

    def qwords(self, begin, end, interpolate=True):
        self.emit("QWORDS_BEGIN")
        tokens = StringLexer(self, begin, end, interpolate=interpolate).tokenize(qwords=True)
        if tokens[-2].name == "STRING_BEGIN": # drop empty last string
            tokens = tokens[:-2]
        self.tokens.extend(tokens)
        self.emit("QWORDS_END")
        self.state = self.EXPR_END

    def percent(self, ch, space_seen):
        c = self.read()
        if self.is_beg() or (self.is_arg() and space_seen and c.isspace()):
            return self.quote(c)
        elif c == "=":
            self.add(ch)
            self.emit("MODULO_EQUAL")
        else:
            self.unread()
            self.add(ch)
            self.set_expression_state()
            self.emit("MODULO")

    def quote(self, ch):
        if not ch.isalnum():
            begin = ch
            ch = "Q"
        else:
            begin = self.read()
            if begin.isalnum():
                self.error()

        if begin == "(":
            end = ")"
        elif begin == "[":
            end = "]"
        elif begin == "{":
            end = "}"
        elif begin == "<":
            end = ">"
        else:
            end = begin

        if ch == "Q":
            tokens = StringLexer(self, begin, end, interpolate=True).tokenize()
            self.tokens.extend(tokens)
        elif ch == "q":
            tokens = StringLexer(self, begin, end, interpolate=False).tokenize()
            self.tokens.extend(tokens)
        elif ch == "x":
            self.shellout(begin, end)
        elif ch == "w":
            self.qwords(begin, end, interpolate=False)
        elif ch == "W":
            self.qwords(begin, end, interpolate=True)
        elif ch == "r":
            self.regexp(begin, end)
        else:
            raise NotImplementedError('%' + ch)
        self.state = self.EXPR_END


class StringLexer(BaseLexer):
    CODE = 0
    STRING = 1

    def __init__(self, lexer, begin, end, interpolate=True):
        BaseLexer.__init__(self)
        self.lexer = lexer

        self.interpolate = interpolate

        self.begin = begin
        self.end = end

        self.nesting = 0

    def get_idx(self):
        return self.lexer.get_idx()

    def get_lineno(self):
        return self.lexer.get_lineno()

    def get_columno(self):
        return self.lexer.get_columno()

    def read(self):
        return self.lexer.read()

    def unread(self):
        return self.lexer.unread()

    def emit_str(self):
        if self.current_value:
            self.emit("STRING_VALUE")

    def tokenize(self, qwords=False):
        if qwords:
            while self.peek().isspace():
                self.read()
        self.emit("STRING_BEGIN")
        while True:
            ch = self.read()
            if ch == self.lexer.EOF:
                self.unread()
                return self.tokens
            elif ch == "\\" and self.peek() in [self.begin, self.end, "\\"]:
                self.add(self.read())
            elif ch == self.begin and (self.begin != self.end):
                self.nesting += 1
                self.add(ch)
            elif ch == self.end:
                if self.nesting == 0:
                    self.emit_str()
                    break
                else:
                    self.nesting -= 1
                    self.add(ch)
            elif ch == "#" and self.peek() == "{" and self.interpolate:
                self.emit_str()
                self.read()
                self.tokenize_interpolation()
            elif qwords and ch.isspace():
                self.emit_str()
                break
            elif qwords and ch == "\\" and self.peek().isspace():
                self.add(self.read())
            else:
                self.add(ch)
        self.emit("STRING_END")
        if qwords and ch.isspace():
            self.tokenize(qwords=True)
        return self.tokens

    def tokenize_interpolation(self):
        self.emit("DSTRING_START")
        chars = []
        context = [self.CODE]
        braces_count = [1]
        while True:
            ch = self.read()
            if ch == self.lexer.EOF:
                self.unread()
                return
            elif ch == "{" and context[-1] == self.CODE:
                chars.append(ch)
                braces_count[-1] += 1
            elif ch == "}" and context[-1] == self.CODE:
                braces_count[-1] -= 1
                if braces_count[-1] == 0:
                    braces_count.pop()
                    context.pop()
                    if not braces_count:
                        break
                chars.append(ch)
            elif ch == '"' and context[-1] == self.STRING:
                chars.append(ch)
                context.pop()
            elif ch == '"' and context[-1] == self.CODE:
                chars.append(ch)
                context.append(self.STRING)
            elif ch == "#" and self.peek() == "{":
                chars.append(ch)
                ch = self.read()
                chars.append(ch)
                braces_count.append(1)
                context.append(self.CODE)
            else:
                chars.append(ch)
        lexer_tokens = Lexer("".join(chars)).tokenize()
        # Remove the EOF
        lexer_tokens.pop()
        self.tokens.extend(lexer_tokens)
        self.emit("DSTRING_END")
