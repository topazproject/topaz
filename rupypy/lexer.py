import string

from pypy.rlib.rstring import StringBuilder

from rply import Token
from rply.token import SourcePosition


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
        "if": Keyword("IF", "IF_MOD", EXPR_BEG),
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
        "and": Keyword("AND", "AND", EXPR_BEG),
        "or": Keyword("OR", "OR", EXPR_BEG),
        "not": Keyword("NOT", "NOT", EXPR_BEG),
        "alias": Keyword("ALIAS", "ALIAS", EXPR_FNAME),
    }

    def __init__(self):
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
        return SourcePosition(self.get_idx(), self.get_lineno(), self.get_columno())

    def emit(self, token):
        value = "".join(self.current_value)
        self.clear()
        return Token(token, value, self.current_pos())

    def error(self):
        raise LexerError(self.current_pos())


class Lexer(BaseLexer):
    def __init__(self, source, initial_lineno):
        BaseLexer.__init__(self)
        self.source = source
        self.idx = 0
        self.lineno = initial_lineno
        self.columno = 1
        self.state = self.EXPR_BEG
        self.paren_nest = 0
        self.left_paren_begin = 0
        self.condition_state = StackState()
        self.cmd_argument_state = StackState()

    def tokenize(self):
        space_seen = False
        while True:
            ch = self.read()
            if ch == self.EOF:
                break
            if ch == " ":
                space_seen = True
                continue
            elif ch == "#":
                self.comment(ch)
            elif ch == "\n":
                space_seen = True
                if self.state != self.EXPR_BEG:
                    self.add(ch)
                    yield self.emit("LITERAL_NEWLINE")
                self.lineno += 1
                self.columno = 1
                self.state = self.EXPR_BEG
                continue
            elif ch == "*":
                for token in self.star(ch, space_seen):
                    yield token
            elif ch == "!":
                for token in self.exclamation(ch):
                    yield token
            elif ch == "=":
                for token in self.equal(ch):
                    yield token
            elif ch == "<":
                for token in self.less_than(ch, space_seen):
                    yield token
            elif ch == ">":
                for token in self.greater_than(ch):
                    yield token
            elif ch == '"':
                for token in StringLexer(self, '"', '"').tokenize():
                    yield token
                self.state = self.EXPR_END
            elif ch == "'":
                for token in self.single_quote(ch):
                    yield token
            elif ch == "?":
                for token in self.question_mark(ch):
                    yield token
            elif ch == "&":
                for token in self.ampersand(ch, space_seen):
                    yield token
            elif ch == "|":
                for token in self.pipe(ch):
                    yield token
            elif ch == "+":
                for token in self.plus(ch):
                    yield token
            elif ch == "-":
                for token in self.minus(ch, space_seen):
                    yield token
            elif ch == ".":
                for token in self.dot(ch):
                    yield token
            elif ch.isdigit():
                for token in self.number(ch):
                    yield token
            elif ch == ")":
                self.add(ch)
                self.state = self.EXPR_ENDFN
                yield self.emit("RPAREN")
            elif ch == "]":
                self.add(ch)
                self.state = self.EXPR_ENDARG
                yield self.emit("RBRACK")
            elif ch == "}":
                self.add(ch)
                yield self.emit("RBRACE")
                self.state = self.EXPR_ENDFN
            elif ch == ":":
                for token in self.colon(ch, space_seen):
                    yield token
            elif ch == "/":
                for token in self.slash(ch, space_seen):
                    yield token
            elif ch == "^":
                self.add(ch)
                self.set_expression_state()
                yield self.emit("CARET")
            elif ch == ";":
                self.add(ch)
                self.state = self.EXPR_BEG
                yield self.emit("LITERAL_SEMICOLON")
            elif ch == ",":
                self.add(ch)
                self.state = self.EXPR_BEG
                yield self.emit("LITERAL_COMMA")
            elif ch == "~":
                self.add(ch)
                self.state = self.EXPR_BEG
                yield self.emit("TILDE")
            elif ch == "(":
                for token in self.left_paren(ch, space_seen):
                    yield token
            elif ch == "[":
                for token in self.left_bracket(ch, space_seen):
                    yield token
            elif ch == "{":
                self.add(ch)
                yield self.emit("LBRACE")
                self.state = self.EXPR_BEG
            elif ch == "\\":
                ch2 = self.read()
                if ch2 == "\n":
                    self.lineno += 1
                    self.columno = 1
                    space_seen = True
                    continue
                raise NotImplementedError
            elif ch == "%":
                for token in self.percent(ch, space_seen):
                    yield token
            elif ch == "$":
                for token in self.dollar(ch):
                    yield token
            elif ch == "@":
                for token in self.at(ch):
                    yield token
            elif ch == "`":
                for token in self.backtick(ch):
                    yield token
            else:
                for token in self.identifier(ch):
                    yield token
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

            if keyword.normal_token == "DO":
                return self.emit_do(state)

            if state in [self.EXPR_BEG, self.EXPR_VALUE]:
                token = self.emit(keyword.normal_token)
            else:
                token = self.emit(keyword.inline_token)
                if keyword.inline_token != keyword.normal_token:
                    self.state = self.EXPR_BEG
        else:
            if value[0].isupper():
                token = self.emit("CONSTANT")
            else:
                token = self.emit("IDENTIFIER")
            if self.is_beg() or self.state == self.EXPR_DOT or self.is_arg():
                self.state = self.EXPR_ARG
            elif self.state == self.EXPR_ENDFN:
                self.state = self.EXPR_ENDFN
            else:
                self.state = self.EXPR_END
        return token

    def emit_do(self, state):
        self.command_start = True

        if self.left_paren_begin > 0 and self.left_paren_begin == self.paren_nest:
            self.left_paren_begin = 0
            self.paren_nest -= 1
            return self.emit("DO_LAMBDA")

        if self.condition_state.is_in_state():
            return self.emit("DO_COND")

        if state != self.EXPR_CMDARG and self.cmd_argument_state.is_in_state():
            return self.emit("DO_BLOCK")
        if state in [self.EXPR_ENDARG, self.EXPR_BEG]:
            return self.emit("DO_BLOCK")
        return self.emit("DO")

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
                yield self.emit_identifier()
                self.unread()
                break
            if ch in "!?" or (ch == "=" and self.state == self.EXPR_FNAME):
                self.add(ch)
                yield self.emit_identifier()
                break
            elif ch.isalnum() or ch == "_":
                self.add(ch)
            else:
                state = self.state
                yield self.emit_identifier()
                if state == self.EXPR_FNAME and ch == ".":
                    self.add(ch)
                    yield self.emit("DOT")
                    self.state = self.EXPR_FNAME
                else:
                    self.unread()
                break

    def number(self, ch):
        self.state = self.EXPR_END
        self.add(ch)
        first_zero = ch == "0"
        is_hex = False
        symbol = "INTEGER"
        while True:
            ch = self.read()
            if ch == self.EOF:
                yield self.emit(symbol)
                self.unread()
                break
            if first_zero and ch.upper() in "XBDO":
                if ch.upper() != "D":
                    self.add(ch.upper())
                is_hex = ch.upper() == "X"
            elif ch == ".":
                if not self.peek().isdigit():
                    yield self.emit(symbol)
                    self.unread()
                    break
                self.add(ch)
                symbol = "FLOAT"
            elif ch.isdigit() or (is_hex and ch.upper() in "ABCDEF"):
                self.add(ch)
            elif ch == "_":
                if not self.peek().isdigit():
                    self.error()
            elif ch.upper() == "E":
                symbol = "FLOAT"
                self.add(ch.upper())
            else:
                yield self.emit(symbol)
                self.unread()
                break
            first_zero = False

    def single_quote(self, ch):
        self.state = self.EXPR_END
        yield self.emit("STRING_BEG")
        while True:
            ch = self.read()
            if ch == self.EOF:
                self.unread()
                break
            elif ch == "'":
                yield self.emit("STRING_CONTENT")
                break
            else:
                self.add(ch)
        yield self.emit("STRING_END")

    def regexp(self, begin, end):
        yield self.emit("REGEXP_BEG")
        for token in StringLexer(self, begin, end, interpolate=True, regexp=True).tokenize():
            yield token
        yield self.emit("REGEXP_END")
        self.state = self.EXPR_END

    def here_doc(self):
        ch = self.read()

        indent = ch == "-"
        interpolate = True
        shellout = True
        if indent:
            ch = self.read()

        if ch in "'\"`":
            term = ch
            if term == "'":
                interpolate = False
            elif term == "`":
                shellout = True

            marker = StringBuilder()
            while True:
                ch = self.read()
                if ch == self.EOF:
                    self.unread()
                    break
                elif ch == term:
                    break
                else:
                    marker.append(ch)
        else:
            if not (ch.isalnum() or ch == "_"):
                self.unread()
                if indent:
                    self.unread()
                return

            marker = StringBuilder()
            marker.append(ch)
            while True:
                ch = self.read()
                if ch == self.EOF or not (ch.isalnum() or ch == "_"):
                    self.unread()
                    break
                marker.append(ch)

        for token in HeredocLexer(self, marker.build(), indent, interpolate=True).tokenize():
            yield token
        self.state = self.EXPR_END

    def dollar(self, ch):
        self.add(ch)
        self.state = self.EXPR_END
        ch = self.read()
        if ch in "$>:?\\!\"":
            self.add(ch)
            yield self.emit("GVAR")
        else:
            self.unread()
            while True:
                ch = self.read()
                if ch.isalnum() or ch == "_":
                    self.add(ch)
                else:
                    self.unread()
                    yield self.emit("GVAR")
                    break

    def at(self, ch):
        self.add(ch)
        ch = self.read()
        if ch == "@":
            self.add(ch)
            token = "CLASS_VAR"
        else:
            self.unread()
            token = "IVAR"
        self.state = self.EXPR_END
        while True:
            ch = self.read()
            if ch.isalnum() or ch == "_":
                self.add(ch)
            else:
                self.unread()
                yield self.emit(token)
                break

    def plus(self, ch):
        self.add(ch)
        ch2 = self.read()
        if ch2 == "=":
            self.add(ch2)
            yield self.emit("PLUS_EQUAL")
        else:
            self.unread()
            self.state = self.EXPR_BEG
            yield self.emit("PLUS")

    def minus(self, ch, space_seen):
        self.add(ch)
        ch2 = self.read()
        if ch2 == "=":
            self.add(ch2)
            self.state = self.EXPR_BEG
            yield self.emit("MINUS_EQUAL")
        elif self.is_beg() or (self.is_arg() and space_seen and not ch2.isspace()):
            self.state = self.EXPR_BEG
            if ch2.isdigit():
                for token in self.number(ch2):
                    yield token
            else:
                self.unread()
                yield self.emit("UNARY_MINUS")
        else:
            self.unread()
            self.state = self.EXPR_BEG
            yield self.emit("MINUS")

    def star(self, ch, space_seen):
        self.add(ch)
        ch2 = self.read()
        if ch2 == "*":
            self.add(ch2)
            ch3 = self.read()
            if ch3 == "=":
                self.add(ch3)
                self.state = self.EXPR_BEG
                yield self.emit("OP_ASGN")
            else:
                self.unread()
                self.set_expression_state()
                yield self.emit("POW")
        elif ch2 == "=":
            self.add(ch2)
            self.state = self.EXPR_BEG
            yield self.emit("OP_ASGN")
        else:
            self.unread()
            if self.is_arg() and space_seen and not ch2.isspace():
                tok_name = "STAR"
            elif self.is_beg():
                tok_name = "STAR"
            else:
                tok_name = "STAR2"
            yield self.emit(tok_name)

    def slash(self, ch, space_seen):
        if self.is_beg():
            for token in self.regexp("/", "/"):
                yield token
        else:
            ch2 = self.read()
            if ch2 == "=":
                self.add(ch)
                self.add(ch2)
                yield self.emit("DIV_EQUAL")
                self.state = self.EXPR_BEG
            else:
                self.unread()
                if self.is_arg() and space_seen and not ch2.isspace():
                    for token in self.regexp("/", "/"):
                        yield token
                else:
                    self.add(ch)
                    self.set_expression_state()
                    yield self.emit("DIVIDE")

    def pipe(self, ch):
        self.add(ch)
        ch2 = self.read()
        if ch2 == "|":
            self.add(ch2)
            self.state = self.EXPR_BEG
            ch3 = self.read()
            if ch3 == "=":
                self.add(ch3)
                yield self.emit("OR_EQUAL")
            else:
                self.unread()
                yield self.emit("OROP")
        elif ch2 == "=":
            self.add(ch2)
            self.state = self.EXPR_BEG
            yield self.emit("PIPE_EQUAL")
        else:
            self.unread()
            self.set_expression_state()
            yield self.emit("PIPE")

    def ampersand(self, ch, space_seen):
        self.add(ch)

        ch2 = self.read()
        if ch2 == "&":
            self.add(ch2)
            self.state = self.EXPR_BEG
            ch3 = self.read()
            if ch3 == "=":
                self.add(ch3)
                yield self.emit("OP_ASGN")
            else:
                self.unread()
                yield self.emit("ANDOP")
        elif ch2 == "=":
            self.add(ch2)
            yield self.emit("OP_ASGN")
        else:
            self.unread()
            if self.is_arg() and space_seen and not ch2.isspace():
                tok = "AMPER"
            elif self.is_beg():
                tok = "AMPER"
            else:
                tok = "AMPER2"
            self.set_expression_state()
            yield self.emit(tok)

    def equal(self, ch):
        self.add(ch)
        self.set_expression_state()
        ch2 = self.read()
        if ch2 == "=":
            self.add(ch2)
            ch3 = self.read()
            if ch3 == "=":
                self.add(ch3)
                yield self.emit("EQQ")
            else:
                self.unread()
                yield self.emit("EQ")
        elif ch2 == "~":
            self.add(ch2)
            yield self.emit("MATCH")
        elif ch2 == ">":
            self.add(ch2)
            yield self.emit("ASSOC")
        else:
            self.unread()
            yield self.emit("LITERAL_EQUAL")

    def less_than(self, ch, space_seen):
        ch2 = self.read()

        if (ch2 == "<" and self.state not in [self.EXPR_DOT, self.EXPR_CLASS] and
            not self.is_end() and (not self.is_arg() or space_seen)):
            tokens_yielded = False
            for token in self.here_doc():
                tokens_yielded = True
                yield token
            if tokens_yielded:
                return

        self.add(ch)
        self.set_expression_state()
        if ch2 == "=":
            self.add(ch2)
            ch3 = self.read()
            if ch3 == ">":
                self.add(ch3)
                yield self.emit("CMP")
            else:
                self.unread()
                yield self.emit("LEQ")
        elif ch2 == "<":
            self.add(ch2)
            yield self.emit("LSHFT")
        else:
            self.unread()
            yield self.emit("LT")

    def greater_than(self, ch):
        self.add(ch)
        self.set_expression_state()
        ch2 = self.read()
        if ch2 == "=":
            self.add(ch2)
            yield self.emit("GEQ")
        elif ch2 == ">":
            self.add(ch2)
            yield self.emit("RSHFT")
        else:
            self.unread()
            yield self.emit("GT")

    def dot(self, ch):
        self.add(ch)
        self.state = self.EXPR_BEG
        ch2 = self.read()
        if ch2 == ".":
            self.add(ch2)
            ch3 = self.read()
            if ch3 == ".":
                self.add(ch3)
                yield self.emit("DOT3")
            else:
                self.unread()
                yield self.emit("DOT2")
        else:
            self.unread()
            self.state = self.EXPR_DOT
            yield self.emit("DOT")

    def exclamation(self, ch):
        self.add(ch)
        self.state = self.EXPR_BEG

        ch2 = self.read()
        if ch2 == "=":
            self.add(ch2)
            yield self.emit("NEQ")
        elif ch2 == "~":
            self.add(ch2)
            yield self.emit("NMATCH")
        else:
            self.unread()
            yield self.emit("BANG")

    def question_mark(self, ch):
        if self.is_end():
            self.add(ch)
            self.state = self.EXPR_VALUE
            yield self.emit("QUESTION")
        else:
            ch2 = self.read()
            if ch2.isspace():
                self.unread()
                self.add(ch)
                self.state = self.EXPR_VALUE
                yield self.emit("QUESTION")
            else:
                if ch2 == "\\":
                    for ch in self.read_escape(character_escape=True):
                        self.add(ch)
                else:
                    self.add(ch2)
                yield self.emit("CHAR")
                self.state = self.EXPR_END

    def read_escape(self, character_escape=False):
        c = self.read()
        if c == self.EOF:
            self.error()
        elif c == "\\":
            return ["\\"]
        elif c == "n":
            return ["\n"]
        elif c == "t":
            return ["\t"]
        elif c == "r":
            return ["\r"]
        elif c == "f":
            return ["\f"]
        elif c == "v":
            return ["\v"]
        elif c == "a":
            return ["\a"]
        elif c == "b":
            return ["\b"]
        elif c == "e":
            return ["\x1b"]
        elif c == "s":
            return [" "]
        elif c == "u":
            raise NotImplementedError("UTF-8 escape not implemented")
        elif c == "x":
            hex_escape = self.read()
            if not hex_escape in string.hexdigits:
                self.error()
            if self.peek() in string.hexdigits:
                hex_escape += self.read()
            return [chr(int(hex_escape, 16))]
        elif c in string.octdigits:
            buf = c
            octal = True
            while self.peek() in string.digits:
                ch2 = self.read()
                if ch2 in string.octdigits:
                    buf += ch2
                elif character_escape:
                    self.error()
                else:
                    octal = False
                    buf += ch2
                if len(buf) > 3 and character_escape:
                    self.error()
            if octal:
                codepoint = int(buf, 8)
                if codepoint > 255:
                    codepoint = codepoint - 256
                return [chr(codepoint)]
            else:
                buf = "0" * (len(buf) - 3) + buf
                prefix_idx = 3
                for i in xrange(3):
                    if buf[i] not in string.octdigits:
                        prefix_idx = i
                        break
                codepoint = int(buf[0:prefix_idx], 8)
                if codepoint > 255:
                    codepoint -= 256
                unicode_chars = [chr(codepoint)]
                unicode_chars += buf[prefix_idx:]
                return unicode_chars
        elif c == "M":
            if self.read() != "-":
                self.error()
            c = self.read()
            if c == "\\":
                c = self.read_escape()
                if len(c) != 1:
                    self.error()
                return [chr(ord(c[0]) & 0x80)]
            elif c == self.EOF:
                self.error()
            else:
                return [chr(ord(c) & 0xff | 0x80)]
        elif c == "C" or c == "c":
            if c == "C" and self.read() != "-":
                self.error()
            c = self.read()
            if c == "?":
                return ['\177']
            elif c == self.EOF:
                self.error()
            else:
                if c == "\\":
                    c = self.read_escape()
                    if len(c) != 1:
                        self.error()
                    [c] = c
                return [chr(ord(c) & 0x9f)]
        return [c]

    def colon(self, ch, space_seen):
        ch2 = self.read()

        self.add(ch)
        if ch2 == ":":
            self.add(ch2)
            if self.is_beg() or self.state == self.EXPR_CLASS or (self.is_arg and space_seen):
                self.state = self.EXPR_BEG
                yield self.emit("COLON3")
            else:
                self.state = self.EXPR_DOT
                yield self.emit("COLON2")
        elif self.is_end() or ch2.isspace():
            self.unread()
            self.state = self.EXPR_BEG
            yield self.emit("LITERAL_COLON")
        else:
            self.unread()
            self.state = self.EXPR_FNAME
            yield self.emit("SYMBEG")

    def left_paren(self, ch, space_seen):
        self.add(ch)
        tok_name = "LPAREN2"
        if self.is_beg():
            tok_name = "LPAREN"
        elif space_seen:
            tok_name = "LPAREN_ARG"
        self.paren_nest += 1
        self.condition_state.stop()
        self.cmd_argument_state.stop()
        self.state = self.EXPR_BEG
        yield self.emit(tok_name)

    def left_bracket(self, ch, space_seen):
        self.paren_nest += 1
        if self.state in [self.EXPR_FNAME, self.EXPR_DOT]:
            self.state = self.EXPR_ARG

            ch2 = self.read()
            if ch2 == "]":
                self.add(ch2)
                ch3 = self.read()
                if ch3 == "=":
                    self.add(ch3)
                    yield self.emit("ASET")
                else:
                    self.unread()
                    yield self.emit("AREF")
            else:
                self.unread()
                yield self.emit("LITERAL_LBRACKET")
        elif (self.is_beg() or (self.is_arg() and space_seen)):
            tok = "LBRACK"
        else:
            tok = "LITERAL_LBRACKET"

        self.state = self.EXPR_BEG
        self.condition_state.stop()
        self.cmd_argument_state.stop()
        yield self.emit(tok)

    def backtick(self, ch):
        if self.state == self.EXPR_FNAME:
            self.add(ch)
            yield self.emit_identifier()
        elif self.state == self.EXPR_DOT:
            raise NotImplementedError("`")
        else:
            for token in self.shellout("`", "`"):
                yield token

    def shellout(self, begin, end):
        yield self.emit("SHELL_BEGIN")
        for token in StringLexer(self, begin, end, interpolate=True).tokenize():
            yield token
        yield self.emit("SHELL_END")
        self.state = self.EXPR_END

    def qwords(self, begin, end, interpolate=True):
        yield self.emit("QWORDS_BEGIN")
        tokens = []
        for token in StringLexer(self, begin, end, interpolate=interpolate, qwords=True).tokenize():
            tokens.append(token)
        # drop empty last string
        n_tokens = len(tokens)
        if n_tokens > 2:
            if tokens[n_tokens - 2].name == "STRING_BEGIN":
                tokens.pop()
                tokens.pop()
        else:
            tokens = []
        for token in tokens:
            yield token
        yield self.emit("QWORDS_END")
        self.state = self.EXPR_END

    def percent(self, ch, space_seen):
        c = self.read()
        if self.is_beg():
            for token in self.quote(c):
                yield token
        elif c == "=":
            self.add(ch)
            self.add(c)
            yield self.emit("MODULO_EQUAL")
        elif self.is_arg() and space_seen and not c.isspace():
            for token in self.quote(c):
                yield token
        else:
            self.unread()
            self.add(ch)
            self.set_expression_state()
            yield self.emit("PERCENT")

    def quote_string(self, begin, end, interpolate):
        yield self.emit("QUOTE_BEGIN")
        for token in  StringLexer(self, begin, end, interpolate=interpolate).tokenize():
            yield token
        yield self.emit("QUOTE_END")

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
            for token in self.quote_string(begin, end, True):
                yield token
        elif ch == "q":
            for token in self.quote_string(begin, end, False):
                yield token
        elif ch == "x":
            for token in self.shellout(begin, end):
                yield token
        elif ch == "w":
            for token in self.qwords(begin, end, interpolate=False):
                yield token
        elif ch == "W":
            for token in self.qwords(begin, end, interpolate=True):
                yield token
        elif ch == "r":
            for token in self.regexp(begin, end):
                yield token
        else:
            raise NotImplementedError('%' + ch)
        self.state = self.EXPR_END


class BaseStringLexer(BaseLexer):
    CODE = 0
    STRING = 1

    def __init__(self, lexer):
        BaseLexer.__init__(self)
        self.lexer = lexer

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

    def read_escape(self):
        return self.lexer.read_escape()

    def emit_str(self):
        if self.current_value:
            return self.emit("STRING_CONTENT")

    def tokenize_interpolation(self):
        yield self.emit("DSTRING_START")
        chars = StringBuilder()
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
        last = None
        for token in Lexer(chars.build(), self.get_lineno()).tokenize():
            if last is not None:
                yield last
            last = token
        yield self.emit("DSTRING_END")


class StringLexer(BaseStringLexer):
    def __init__(self, lexer, begin, end, interpolate=True, qwords=False, regexp=False):
        BaseStringLexer.__init__(self, lexer)

        self.interpolate = interpolate
        self.qwords = qwords
        self.regexp = regexp

        self.begin = begin
        self.end = end

        self.nesting = 0

    def tokenize(self):
        if self.qwords:
            while self.peek().isspace():
                self.read()
        if not self.regexp:
            yield self.emit("STRING_BEGIN")
        while True:
            ch = self.read()
            if ch == self.lexer.EOF:
                self.unread()
                break
            elif ch == "\\":
                if self.peek() in [self.begin, self.end, "\\"]:
                    self.add(self.read())
                else:
                    escaped_char = self.read_escape()
                    if (self.regexp and len(escaped_char) == 1 and
                        escaped_char[0] in string.printable):
                        self.add(ch)
                        self.add(escaped_char[0])
                    else:
                        for c in escaped_char:
                            self.add(c)
            elif ch == self.begin and (self.begin != self.end):
                self.nesting += 1
                self.add(ch)
            elif ch == self.end:
                if self.nesting == 0:
                    token = self.emit_str()
                    if token:
                        yield token
                    break
                else:
                    self.nesting -= 1
                    self.add(ch)
            elif ch == "#" and self.peek() == "{" and self.interpolate:
                token = self.emit_str()
                if token:
                    yield token
                self.read()
                for token in self.tokenize_interpolation():
                    yield token
            elif self.qwords and ch.isspace():
                token = self.emit_str()
                if token:
                    yield token
                break
            elif self.qwords and ch == "\\" and self.peek().isspace():
                self.add(self.read())
            else:
                self.add(ch)
        if not self.regexp:
            yield self.emit("STRING_END")
        if self.qwords and ch.isspace():
            for token in self.tokenize():
                yield token


class HeredocLexer(BaseStringLexer):
    def __init__(self, lexer, marker, indent, interpolate):
        BaseStringLexer.__init__(self, lexer)
        self.marker = marker
        self.indent = indent
        self.interpolate = interpolate

    def tokenize(self):
        chars = StringBuilder()
        while True:
            ch = self.read()
            if ch == "\n":
                break
            elif ch == self.EOF:
                return
            chars.append(ch)
        if chars.getlength():
            lexer_tokens = []
            for token in Lexer(chars.build(), self.get_lineno()).tokenize():
                lexer_tokens.append(token)
            lexer_tokens.pop()
        else:
            lexer_tokens = []

        yield self.emit("STRING_BEGIN")
        while True:
            ch = self.read()
            if ch == "\n":
                self.add(ch)
                chars = StringBuilder(len(self.marker))
                if self.indent:
                    while True:
                        ch = self.read()
                        if ch.isspace():
                            chars.append(ch)
                        else:
                            self.unread()
                            break
                for c in self.marker:
                    ch = self.read()
                    chars.append(ch)
                    if ch != c:
                        for c in chars.build():
                            self.add(c)
                        break
                else:
                    yield self.emit("STRING_CONTENT")
                    break
            elif ch == "#" and self.peek() == "{":
                token = self.emit_str()
                if token:
                    yield token
                self.read()
                for token in self.tokenize_interpolation():
                    yield token
            elif ch == self.EOF:
                return
            else:
                self.add(ch)
        yield self.emit("STRING_END")
        for token in lexer_tokens:
            yield token


class StackState(object):
    def __init__(self):
        self._stack = 0

    def begin(self):
        orig = self._stack
        self._stack <<= 1
        self._stack |= 1
        return orig

    def stop(self):
        self._stack <<= 1

    def reset(self, orig):
        self._stack = orig

    def is_in_state(self):
        return (self._stack & 1) != 0
