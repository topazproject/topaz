from pypy.rlib.parsing.lexer import Token, SourcePos


class LexerError(Exception):
    def __init__(self, pos):
        self.pos = pos


class Keyword(object):
    def __init__(self, normal_token, inline_token, state):
        self.normal_token = normal_token
        self.inline_token = inline_token
        self.state = state


class Lexer(object):
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

    def __init__(self, source):
        self.source = source
        self.idx = 0
        self.lineno = 1
        self.columno = 1
        self.tokens = []
        self.current_value = []
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
                StringLexer(self).tokenize()
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
                self.slash(ch)
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
                assert False
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
                self.add(ch)
                self.set_expression_state()
                self.emit("MODULO")
            elif ch == "$":
                self.dollar(ch)
            elif ch == "@":
                self.add(ch)
                self.emit("AT_SIGN")
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

    def peek(self):
        ch = self.read()
        self.unread()
        return ch

    def add(self, ch):
        self.current_value.append(ch)

    def clear(self):
        del self.current_value[:]

    def current_pos(self):
        return SourcePos(self.idx, self.lineno, self.columno)

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

    def emit(self, token):
        value = "".join(self.current_value)
        self.clear()
        self.tokens.append(Token(token, value, self.current_pos()))

    def emit_identifier(self):
        value = "".join(self.current_value)
        state = self.state
        if value in self.keywords and self.state != self.EXPR_DOT:
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

    def regexp(self):
        self.state = self.EXPR_END
        while True:
            ch = self.read()
            if ch == self.EOF:
                self.unread()
                break
            elif ch == "/":
                self.emit("REGEXP")
                break
            else:
                self.add(ch)

    def dollar(self, ch):
        self.add(ch)
        self.state = self.EXPR_END
        while True:
            ch = self.read()
            if ch == self.EOF:
                self.emit("GLOBAL")
                self.unread()
                break
            elif ch in ">:":
                self.add(ch)
                self.emit("GLOBAL")
                break
            elif ch.isalnum() or ch == "_":
                self.add(ch)
            else:
                self.unread()
                self.emit("GLOBAL")
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
        else:
            self.unread()
            if self.is_beg() or (self.is_arg() and space_seen and not ch2.isspace()):
                self.emit("UNARY_STAR")
            else:
                self.emit("MUL")
            self.set_expression_state()

    def slash(self, ch):
        if self.is_beg():
            self.regexp()
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
                    self.regexp()
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
                self.add(ch2)
                self.emit("SSTRING")
                self.state = self.EXPR_END

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
            self.add(ch2)
            self.state = self.EXPR_END
            while True:
                ch = self.read()
                if ch.isalnum() or ch == "_":
                    self.add(ch)
                else:
                    self.unread()
                    self.emit("SYMBOL")
                    break

    def left_bracket(self, ch, space_seen):
        self.add(ch)
        if self.is_beg() or (self.is_arg() and space_seen):
            self.emit("LBRACKET")
        else:
            self.emit("LSUBSCRIPT")
        self.state = self.EXPR_BEG


class StringLexer(object):
    def __init__(self, lexer):
        self.lexer = lexer

    def tokenize(self):
        self.lexer.emit("STRING_BEGIN")
        while True:
            ch = self.lexer.read()
            if ch == self.lexer.EOF:
                self.lexer.unread()
                break
            elif ch == '"':
                break
            else:
                self.lexer.add(ch)
        self.lexer.emit("STRING_VALUE")
        self.lexer.emit("STRING_END")
        self.lexer.state = self.lexer.EXPR_END
