import string

from rpython.rlib.rstring import StringBuilder
from rpython.rlib.runicode import unicode_encode_utf_8

from rply import Token
from rply.token import SourcePosition


class LexerError(Exception):
    def __init__(self, pos, msg=None):
        self.pos = pos
        self.msg = "" if msg is None else msg


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
    EXPR_ENDFN = 9
    EXPR_LABEL = 10
    EXPR_LABELED = 11
    EXPR_FITEM = 12

    EXPR_VALUE = EXPR_BEG
    EXPR_BEG_ANY = (EXPR_BEG, EXPR_MID, EXPR_CLASS)
    EXPR_ARG_ANY = (EXPR_ARG, EXPR_CMDARG)
    EXPR_END_ANY = (EXPR_END, EXPR_ENDARG, EXPR_ENDFN)

    keywords = {
        "return": Keyword("RETURN", "RETURN", EXPR_MID),
        "yield": Keyword("YIELD", "YIELD", EXPR_ARG),
        "if": Keyword("IF", "IF_MOD", EXPR_BEG),
        "unless": Keyword("UNLESS", "UNLESS_MOD", EXPR_BEG),
        "then": Keyword("THEN", "THEN", EXPR_BEG),
        "elsif": Keyword("ELSIF", "ELSIF", EXPR_BEG),
        "else": Keyword("ELSE", "ELSE", EXPR_BEG),
        "while": Keyword("WHILE", "WHILE_MOD", EXPR_BEG),
        "until": Keyword("UNTIL", "UNTIL_MOD", EXPR_BEG),
        "for": Keyword("FOR", "FOR", EXPR_BEG),
        "in": Keyword("IN", "IN", EXPR_BEG),
        "do": Keyword("DO", "DO", EXPR_BEG),
        "begin": Keyword("BEGIN", "BEGIN", EXPR_BEG),
        "rescue": Keyword("RESCUE", "RESCUE_MOD", EXPR_MID),
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
        "self": Keyword("SELF", "SELF", EXPR_END),
        "nil": Keyword("NIL", "NIL", EXPR_END),
        "__FILE__": Keyword("__FILE__", "__FILE__", EXPR_END),
        "__LINE__": Keyword("__LINE__", "__LINE__", EXPR_END),
        "true": Keyword("TRUE", "TRUE", EXPR_END),
        "false": Keyword("FALSE", "FALSE", EXPR_END),
        "defined?": Keyword("DEFINED", "DEFINED", EXPR_ARG),
        "super": Keyword("SUPER", "SUPER", EXPR_ARG),
        "undef": Keyword("UNDEF", "UNDEF", EXPR_FNAME),
        "next": Keyword("NEXT", "NEXT", EXPR_MID),
        "break": Keyword("BREAK", "BREAK", EXPR_MID),
    }

    def __init__(self, source, initial_lineno, symtable):
        self.source = source
        self.lineno = initial_lineno
        self.symtable = symtable
        self.current_value = []
        self.idx = 0
        self.columno = 1
        self.state = self.EXPR_BEG
        self.label_state = 0
        self.paren_nest = 0
        self.left_paren_begin = 0
        self.command_start = True
        self.condition_state = StackState()
        self.cmd_argument_state = StackState()
        self.str_term = None

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self.label_state = 0
        self._state = value

    def peek(self):
        ch = self.read()
        self.unread()
        return ch

    def add(self, ch):
        self.current_value.append(ch)

    def clear(self):
        del self.current_value[:]

    def current_pos(self):
        return SourcePosition(self.idx, self.lineno, self.columno)

    def newline(self, ch):
        if ch == "\r" and self.peek() == "\n":
            self.read()
        self.lineno += 1
        self.columno = 1

    def emit(self, token):
        value = "".join(self.current_value)
        self.clear()
        return Token(token, value, self.current_pos())

    def error(self, msg=None):
        raise LexerError(self.current_pos(), msg)

    def tokenize(self):
        space_seen = False
        newline_seen = True
        while True:
            if self.str_term is not None:
                tok = self.str_term.next()
                toktype = tok.gettokentype()
                if toktype == "STRING_END":
                    if (((self.state in [self.EXPR_BEG, self.EXPR_ENDFN] and self.condition_state.is_in_state()) or self.is_arg()) and
                        self.is_label_suffix()):
                        tok = self.emit("LABEL_END")
                toktype = tok.gettokentype()
                if toktype in ["STRING_END", "REGEXP_END", "LABEL_END"]:
                    self.str_term = None
                    if toktype == "LABEL_END":
                        self.state = self.EXPR_BEG
                        self.label_state = self.EXPR_LABEL
                    else:
                        self.state = self.EXPR_END
                yield tok
                continue

            command_state = self.command_start
            self.command_start = False
            ch = self.read()
            if ch == self.EOF:
                break
            if ch in " \t":
                space_seen = True
                newline_seen = False
                continue
            elif ch == "#":
                self.comment(ch)
            elif ch in "\r\n":
                space_seen = newline_seen = True
                self.newline(ch)

                if (self.state not in [self.EXPR_BEG, self.EXPR_DOT,
                                      self.EXPR_VALUE, self.EXPR_FNAME,
                                      self.EXPR_CLASS] and self.label_state != self.EXPR_LABELED):
                    while self.peek() in "\r\n \t\f\v":
                        ch = self.read()
                        if ch in "\r\n":
                            self.newline(ch)
                    if self.peek() in "&.":
                        space_seen = newline_seen = False
                        ch = self.read()
                        ch2 = self.peek()
                        self.unread()
                        if ch == "&" and ch2 != ".":
                            pass
                        else:
                            continue
                    self.add("\n")
                    self.command_start = True
                    self.state = self.EXPR_BEG
                    yield self.emit("LITERAL_NEWLINE")
                continue
            elif ch == "*":
                for token in self.star(ch, space_seen):
                    yield token
            elif ch == "!":
                for token in self.exclamation(ch):
                    yield token
            elif ch == "=":
                if newline_seen:
                    for token in self.multiline_comment(ch):
                        yield token
                else:
                    for token in self.equal(ch):
                        yield token
            elif ch == "<":
                for token in self.less_than(ch, space_seen):
                    yield token
            elif ch == ">":
                for token in self.greater_than(ch):
                    yield token
            elif ch == '"':
                for token in self.double_quote(ch):
                    yield token
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
                for token in self.plus(ch, space_seen):
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
                for token in self.right_paren(ch):
                    yield token
            elif ch == "]":
                for token in self.right_bracket(ch):
                    yield token
            elif ch == "}":
                for token in self.right_brace(ch):
                    yield token
            elif ch == ":":
                for token in self.colon(ch, space_seen):
                    yield token
            elif ch == "/":
                for token in self.slash(ch, space_seen):
                    yield token
            elif ch == "^":
                for token in self.caret(ch):
                    yield token
            elif ch == ";":
                self.add(ch)
                self.state = self.EXPR_BEG
                yield self.emit("LITERAL_SEMICOLON")
            elif ch == ",":
                self.add(ch)
                self.state = self.EXPR_BEG
                self.label_state = self.EXPR_LABEL
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
                for token in self.left_brace(ch):
                    yield token
            elif ch == "\\":
                ch2 = self.read()
                if ch2 in "\r\n":
                    self.newline(ch2)
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
                for token in self.backtick(ch, command_state):
                    yield token
            else:
                for token in self.identifier(ch, command_state):
                    yield token
            space_seen = False
            newline_seen = False

    def read(self):
        try:
            ch = self.source[self.idx]
        except IndexError:
            ch = self.EOF
        self.idx += 1
        self.columno += 1
        return ch

    def unread(self):
        idx = self.idx - 1
        assert idx >= 0
        self.idx = idx
        self.columno -= 1

    def is_label_suffix(self):
        ch = self.read()
        ch2 = self.peek()
        if ch == ":" and ch2 != ":":
            return True
        else:
            self.unread()
            return False

    def is_beg(self):
        return (self.state in self.EXPR_BEG_ANY or
                (self.state == self.EXPR_ARG and
                 self.label_state == self.EXPR_LABELED))

    def is_arg(self):
        return self.state in self.EXPR_ARG_ANY

    def is_end(self):
        return self.state in self.EXPR_END_ANY

    def is_label_possible(self, command_state):
        return (((self.label_state == self.EXPR_LABEL or self.state == self.EXPR_ENDFN) and not command_state) or self.is_arg())

    def set_expression_state(self):
        if self.state in [self.EXPR_FNAME, self.EXPR_DOT]:
            self.state = self.EXPR_ARG
        else:
            self.state = self.EXPR_BEG

    def emit_identifier(self, command_state, token_name="IDENTIFIER"):
        value = "".join(self.current_value)
        state = self.state
        if self.is_label_possible(command_state) and self.is_label_suffix():
            self.state = self.EXPR_ARG
            self.label_state = self.EXPR_LABELED
            return self.emit("LABEL")
        elif value in self.keywords and self.state != self.EXPR_DOT:
            keyword = self.keywords[value]

            if keyword.normal_token == "NOT":
                self.state = self.EXPR_ARG
            else:
                self.state = keyword.state

            if state != self.EXPR_FNAME and keyword.normal_token == "DO":
                return self.emit_do(state)

            if state in [self.EXPR_BEG, self.EXPR_VALUE] or self.label_state == self.EXPR_LABELED:
                token = self.emit(keyword.normal_token)
            else:
                token = self.emit(keyword.inline_token)
                if keyword.inline_token != keyword.normal_token:
                    self.state = self.EXPR_BEG
                    self.label_state = self.EXPR_LABEL
        else:
            if (state == self.EXPR_BEG and not command_state) or self.is_arg():
                ch = self.read()
                if ch == ":" and self.peek() != ":":
                    self.state = self.EXPR_BEG
                    return self.emit("LABEL")
                self.unread()
            if value[0].isupper():
                token = self.emit("CONSTANT")
            else:
                token = self.emit(token_name)
            if self.is_beg() or self.state == self.EXPR_DOT or self.is_arg():
                if command_state:
                    self.state = self.EXPR_CMDARG
                else:
                    self.state = self.EXPR_ARG
            elif self.state == self.EXPR_ENDFN:
                self.state = self.EXPR_ENDFN
            else:
                self.state = self.EXPR_END
        if token.gettokentype() == "IDENTIFIER" and self.symtable.is_defined(token.getstr()):
            self.state = self.EXPR_END
            self.label_state = self.EXPR_LABEL
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
            if ch == self.EOF or ch in "\r\n":
                self.unread()
                break

    def multiline_comment(self, ch):
        read = 0
        for ch in "begin":
            read += 1
            if self.read() == ch:
                break
        else:
            for i in xrange(read):
                self.unread()
            for token in self.equal(ch):
                yield token
            return
        while True:
            ch = self.read()
            if ch == self.EOF:
                self.error("embedded document meets end of file")
            if ch in "\r\n":
                self.newline(ch)
                if (self.read() == "=" and
                    self.read() == "e" and
                    self.read() == "n" and
                    self.read() == "d"):
                    break

    def identifier(self, ch, command_state):
        self.add(ch)
        while True:
            ch = self.read()
            if ch == self.EOF:
                yield self.emit_identifier(command_state)
                self.unread()
                break
            if ch in "!?" or (ch == "=" and self.state == self.EXPR_FNAME and self.peek() not in "~>"):
                self.add(ch)
                yield self.emit_identifier(command_state, "FID")
                break
            elif ch.isalnum() or ch == "_" or ord(ch) > 127:
                self.add(ch)
            else:
                self.unread()
                yield self.emit_identifier(command_state)
                break

    def number(self, ch):
        self.state = self.EXPR_END
        self.add(ch)
        first_zero = ch == "0"
        is_hex = False
        is_octal = False
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
                is_octal = ch.upper() == "O"
            elif first_zero and ch.isdigit():
                is_octal = True
                self.add("O")
                self.add(ch)
            elif ch == ".":
                if not self.peek().isdigit():
                    yield self.emit(symbol)
                    self.unread()
                    break
                self.add(ch)
                symbol = "FLOAT"
            elif ch.isdigit() or (is_hex and ch.upper() in "ABCDEF"):
                if is_octal and ch > "7":
                    self.error()
                self.add(ch)
            elif ch == "_":
                if not (self.peek().isdigit() or (is_hex and self.peek().upper() in "ABCDEF")):
                    self.error()
            elif ch.upper() == "E":
                symbol = "FLOAT"
                self.add(ch.upper())
                if self.peek() in "-+":
                    self.add(self.read())
            elif ch == "i":
                symbol = "IMAGINARY"
                self.add(ch)
            elif ch == "r":
                symbol = "RATIONAL"
                self.add(ch)
            else:
                yield self.emit(symbol)
                self.unread()
                break
            first_zero = False

    def double_quote(self, ch):
        self.str_term = StringTerm(self, "\0", ch)
        yield self.emit("STRING_BEG")

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
            elif ch == "\\":
                ch2 = self.peek()
                if ch2 in "\\'":
                    ch = self.read()
                self.add(ch)
            else:
                self.add(ch)
        yield self.emit("STRING_END")

    def here_doc(self):
        ch = self.read()

        indent = ch == "-"
        expand = True
        regexp = False
        if indent:
            ch = self.read()

        if ch in "'\"`":
            term = ch
            if term == "'":
                expand = False
            elif term == "`":
                regexp = True

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

        last_line = StringBuilder()
        while True:
            ch = self.read()
            if ch in "\r\n":
                self.newline(ch)
                break
            elif ch == self.EOF:
                self.unread()
                break
            last_line.append(ch)

        self.str_term = HeredocTerm(self, marker.build(), last_line.build(), indent=indent, expand=expand)
        if regexp:
            yield self.emit("XSTRING_BEG")
        else:
            yield self.emit("STRING_BEG")

    def dollar(self, ch):
        self.add(ch)
        self.state = self.EXPR_END
        ch = self.read()
        if ch in "$<>:?\\!\"~&`'+/.,@;":
            self.add(ch)
            yield self.emit("GVAR")
        elif ch == "-" and self.peek().isalnum():
            self.add(ch)
            self.add(self.read())
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
            token = "CVAR"
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

    def plus(self, ch, space_seen):
        self.add(ch)
        ch2 = self.read()
        if self.state in [self.EXPR_FNAME, self.EXPR_DOT]:
            self.state = self.EXPR_ARG
            if ch2 == "@":
                self.add(ch2)
                yield self.emit("UPLUS")
            else:
                self.unread()
                yield self.emit("PLUS")
        elif ch2 == "=":
            self.add(ch2)
            self.state = self.EXPR_BEG
            yield self.emit("OP_ASGN")
        elif self.is_beg() or (self.is_arg() and space_seen and not ch2.isspace()):
            self.state = self.EXPR_BEG
            if ch2.isdigit():
                self.clear()
                for token in self.number(ch2):
                    yield token
            else:
                self.unread()
                yield self.emit("UPLUS")
        else:
            self.unread()
            self.state = self.EXPR_BEG
            yield self.emit("PLUS")

    def minus(self, ch, space_seen):
        self.add(ch)
        ch2 = self.read()
        if self.state in [self.EXPR_FNAME, self.EXPR_DOT]:
            self.state = self.EXPR_ARG
            if ch2 == "@":
                self.add(ch2)
                yield self.emit("UMINUS")
            else:
                self.unread()
                yield self.emit("MINUS")
        elif ch2 == "=":
            self.add(ch2)
            self.state = self.EXPR_BEG
            yield self.emit("OP_ASGN")
        elif ch2 == ">":
            self.add(ch2)
            self.state = self.EXPR_ARG
            yield self.emit("LAMBDA")
        elif self.is_beg() or (self.is_arg() and space_seen and not ch2.isspace()):
            self.state = self.EXPR_BEG
            self.unread()
            if ch2.isdigit():
                yield self.emit("UMINUS_NUM")
            else:
                yield self.emit("UMINUS")
        else:
            self.state = self.EXPR_BEG
            self.unread()
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
                if self.is_arg() and space_seen and not ch3.isspace():
                    tok_name = "DSTAR"
                elif self.is_beg():
                    tok_name = "DSTAR"
                else:
                    tok_name = "POW"
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
            self.set_expression_state()
            yield self.emit(tok_name)

    def slash(self, ch, space_seen):
        if self.is_beg():
            self.str_term = StringTerm(self, "\0", "/", is_regexp=True)
            yield self.emit("REGEXP_BEG")
        else:
            ch2 = self.read()
            if ch2 == "=":
                self.add(ch)
                self.add(ch2)
                self.state = self.EXPR_BEG
                yield self.emit("OP_ASGN")
            else:
                self.unread()
                if self.is_arg() and space_seen and not ch2.isspace():
                    self.str_term = StringTerm(self, "\0", "/", is_regexp=True)
                    yield self.emit("REGEXP_BEG")
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
                yield self.emit("OP_ASGN")
            else:
                self.unread()
                yield self.emit("OROP")
        elif ch2 == "=":
            self.add(ch2)
            self.state = self.EXPR_BEG
            yield self.emit("OP_ASGN")
        else:
            self.unread()
            self.set_expression_state()
            if self.state not in [self.EXPR_FNAME, self.EXPR_DOT]:
                self.label_state = self.EXPR_LABEL
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
            self.state = self.EXPR_BEG
            yield self.emit("OP_ASGN")
        elif ch2 == ".":
            self.add(ch2)
            self.state = self.EXPR_DOT
            yield self.emit("ANDDOT")
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

    def caret(self, ch):
        self.add(ch)

        ch2 = self.read()
        if ch2 == "=":
            self.add(ch2)
            self.state = self.EXPR_BEG
            yield self.emit("OP_ASGN")
        else:
            self.unread()
            self.set_expression_state()
            yield self.emit("CARET")

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
            not self.is_end() and (not self.is_arg() or self.label_state == self.EXPR_LABELED or space_seen)):
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
            ch3 = self.read()
            if ch3 == "=":
                self.add(ch3)
                self.state = self.EXPR_BEG
                yield self.emit("OP_ASGN")
            else:
                self.unread()
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
            ch3 = self.read()
            if ch3 == "=":
                self.add(ch3)
                self.state = self.EXPR_BEG
                yield self.emit("OP_ASGN")
            else:
                self.unread()
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
            yield self.emit("LITERAL_QUESTION_MARK")
        else:
            ch2 = self.read()
            if ch2.isspace():
                self.unread()
                self.add(ch)
                self.state = self.EXPR_VALUE
                yield self.emit("LITERAL_QUESTION_MARK")
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
        elif c in "\r\n":
            self.newline(c)
            return ["\n"]
        elif c == "u":
            ch = self.peek()
            brace_seen = (ch == "{")
            if brace_seen:
                self.read()
            return self.read_utf_escape(brace_seen=brace_seen, character_escape=character_escape)
        elif c == "x":
            hex_escape = self.read()
            if hex_escape not in string.hexdigits:
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
                codepoint = int(buf, 8) & 255
                return [chr(codepoint)]
            else:
                buf = "0" * (len(buf) - 3) + buf
                prefix_idx = 3
                for i in xrange(3):
                    if buf[i] not in string.octdigits:
                        prefix_idx = i
                        break
                codepoint = int(buf[:prefix_idx], 8) & 255
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
                return [chr(ord(c[0]) | 0x80)]
            elif c == self.EOF:
                self.error()
            else:
                return [chr(ord(c) & 0xff | 0x80)]
        elif c == "C" or c == "c":
            if c == "C" and self.read() != "-":
                self.error()
            c = self.read()
            if c == "?":
                return ["\177"]
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

    def read_utf_escape(self, brace_seen=False, character_escape=False):
        if not brace_seen:
            utf_escape = []
            for i in xrange(4):
                ch = self.read()
                if ch not in string.hexdigits:
                    self.error("invalid Unicode escape")
                utf_escape.append(ch)
            return self.encode_utf_escape(utf_escape)
        elif character_escape:
            ch = self.read()
            if ch not in string.hexdigits:
                self.error("invalid Unicode escape")
            res = self.read_delimited_utf_escape(ch)
            ch = self.read()
            if ch != "}":
                self.error("unterminated Unicode escape")
            return res
        else:
            chars = []
            ch = self.read()
            while ch in string.hexdigits:
                chars += self.read_delimited_utf_escape(ch)
                ch = self.read()
                if ch.isspace():
                    ch = self.read()
                else:
                    break
            if not chars:
                self.error("invalid Unicode escape")
            if ch != "}":
                self.error("unterminated Unicode escape")
            return chars

    def read_delimited_utf_escape(self, ch):
        utf_escape = [ch]
        ch = self.read()
        while ch in string.hexdigits:
            utf_escape.append(ch)
            ch = self.read()
        self.unread()
        return self.encode_utf_escape(utf_escape)

    def encode_utf_escape(self, utf_escape):
        utf_codepoint = int("".join(utf_escape), 16)
        if utf_codepoint > 0x101111:
            self.error("invalid Unicode codepoint (too large)")
        return [c for c in unicode_encode_utf_8(unichr(utf_codepoint), 1, "ignore")]

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
            if ch2 == "'":
                self.str_term = StringTerm(self, "\0", ch2, expand=False)
            elif ch2 == '"':
                self.str_term = StringTerm(self, "\0", ch2)
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
            if self.is_arg():
                tok_name = "LPAREN_ARG"
        self.paren_nest += 1
        self.condition_state.stop()
        self.cmd_argument_state.stop()
        self.state = self.EXPR_BEG
        self.label_state = self.EXPR_LABEL
        yield self.emit(tok_name)

    def right_paren(self, ch):
        self.paren_nest -= 1
        self.condition_state.restart()
        self.cmd_argument_state.restart()
        self.state = self.EXPR_ENDFN
        yield self.emit("RPAREN")

    def left_bracket(self, ch, space_seen):
        self.paren_nest += 1
        if self.state in [self.EXPR_FNAME, self.EXPR_DOT]:  # IS_AFTER_OPERATOR
            self.state = self.EXPR_ARG

            ch2 = self.read()
            if ch2 == "]":
                self.add(ch)
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
                self.label_state = self.EXPR_LABEL
                yield self.emit("LITERAL_LBRACKET")
        else:
            if (self.is_beg() or (self.is_arg() and space_seen)):
                tok = "LBRACK"
            else:
                tok = "LITERAL_LBRACKET"

            self.state = self.EXPR_BEG
            self.label_state = self.EXPR_LABEL
            self.condition_state.stop()
            self.cmd_argument_state.stop()
            yield self.emit(tok)

    def right_bracket(self, ch):
        self.add(ch)
        self.paren_nest -= 1
        self.condition_state.restart()
        self.cmd_argument_state.restart()
        self.state = self.EXPR_ENDARG
        yield self.emit("RBRACK")

    def left_brace(self, ch):
        self.add(ch)
        if self.left_paren_begin > 0 and self.left_paren_begin == self.paren_nest:
            self.state = self.EXPR_BEG
            self.left_paren_begin = 0
            self.paren_nest -= 1
            self.condition_state.stop()
            self.cmd_argument_state.stop()
            yield self.emit("LAMBEG")
        else:
            if self.label_state == self.EXPR_LABELED:
                tok = "LBRACE"
            elif self.is_arg() or self.state in [self.EXPR_END, self.EXPR_ENDFN]:
                tok = "LCURLY"
                self.command_start = True
            elif self.state == self.EXPR_ENDARG:
                tok = "LBRACE_ARG"
                self.command_start = True
            else:
                tok = "LBRACE"
            self.condition_state.stop()
            self.cmd_argument_state.stop()
            self.state = self.EXPR_BEG
            if tok != "LBRACE_ARG":
                self.label_state = self.EXPR_LABEL
            yield self.emit(tok)

    def right_brace(self, ch):
        self.add(ch)
        self.condition_state.restart()
        self.cmd_argument_state.restart()
        self.state = self.EXPR_ENDARG
        yield self.emit("RCURLY")

    def backtick(self, ch, command_state):
        self.add(ch)

        if self.state == self.EXPR_FNAME:
            self.state = self.EXPR_ENDFN
            yield self.emit("BACK_REF2")
        elif self.state == self.EXPR_DOT:
            self.state = self.EXPR_CMDARG if command_state else self.EXPR_ARG
            yield self.emit("BACK_REF2")
        else:
            self.str_term = StringTerm(self, "\0", "`")
            yield self.emit("XSTRING_BEG")

    def percent(self, ch, space_seen):
        c = self.read()
        if self.is_beg():
            for token in self.quote(c):
                yield token
        elif c == "=":
            self.add(ch)
            self.add(c)
            self.state = self.EXPR_BEG
            yield self.emit("OP_ASGN")
        elif self.is_arg() and space_seen and not c.isspace():
            for token in self.quote(c):
                yield token
        else:
            self.unread()
            self.add(ch)
            self.set_expression_state()
            yield self.emit("PERCENT")

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
            begin = "\0"

        if ch == "Q":
            self.str_term = StringTerm(self, begin, end)
            yield self.emit("STRING_BEG")
        elif ch == "q":
            self.str_term = StringTerm(self, begin, end, expand=False)
            yield self.emit("STRING_BEG")
        elif ch == "x":
            self.str_term = StringTerm(self, begin, end)
            yield self.emit("XSTRING_BEG")
        elif ch == "W":
            self.str_term = StringTerm(self, begin, end, expand=True, is_qwords=True)
            while True:
                ch = self.read()
                if not ch.isspace():
                    break
            self.unread()
            yield self.emit("WORDS_BEG")
        elif ch == "w":
            self.str_term = StringTerm(self, begin, end, expand=False, is_qwords=True)
            while True:
                ch = self.read()
                if not ch.isspace():
                    break
            self.unread()
            yield self.emit("QWORDS_BEG")
        elif ch == "I":
            self.str_term = StringTerm(self, begin, end, expand=True, is_qwords=True)
            while True:
                ch = self.read()
                if not ch.isspace():
                    break
            self.unread()
            yield self.emit("SYMBOLS_BEG")
        elif ch == "i":
            self.str_term = StringTerm(self, begin, end, expand=False, is_qwords=True)
            while True:
                ch = self.read()
                if not ch.isspace():
                    break
            self.unread()
            yield self.emit("QSYMBOLS_BEG")
        elif ch == "r":
            self.str_term = StringTerm(self, begin, end, is_regexp=True)
            yield self.emit("REGEXP_BEG")
        elif ch == "s":
            self.str_term = StringTerm(self, begin, end, expand=False)
            self.state = self.EXPR_FNAME
            yield self.emit("SYMBEG")
        else:
            raise NotImplementedError("%" + ch)


class BaseStringTerm(object):
    def __init__(self, lexer, expand):
        self.lexer = lexer
        self.expand = expand
        self.is_end = False


class StringTerm(BaseStringTerm):
    def __init__(self, lexer, begin, end_char, expand=True, is_regexp=False, is_qwords=False):
        BaseStringTerm.__init__(self, lexer, expand=expand)
        self.begin = begin
        self.end_char = end_char
        self.is_regexp = is_regexp
        self.is_qwords = is_qwords
        self.nest = 0

    def next(self):
        if self.is_end:
            return self.lexer.emit("STRING_END")
        ch = self.lexer.read()
        if ch == self.lexer.EOF:
            self.lexer.error()
        space_seen = False
        if self.is_qwords and ch.isspace():
            while ch.isspace():
                if ch in "\r\n":
                    self.lexer.newline(ch)
                ch = self.lexer.read()
            space_seen = True

        if ch == self.end_char and self.nest == 0:
            return self.end_found()

        if space_seen:
            self.lexer.unread()
            return self.lexer.emit("LITERAL_SPACE")

        if self.expand and ch == "#":
            self.lexer.add(ch)
            ch = self.lexer.read()
            if ch in ["$", "@"]:
                self.lexer.unread()
                return self.lexer.emit("STRING_DVAR")
            elif ch == "{":
                self.lexer.add(ch)
                return self.lexer.emit("STRING_DBEG")
        self.lexer.unread()

        while True:
            ch = self.lexer.read()
            if ch == self.lexer.EOF:
                break
            if self.begin != "\0" and ch == self.begin:
                self.lexer.add(ch)
                self.nest += 1
            elif ch == self.end_char:
                if self.nest == 0:
                    self.lexer.unread()
                    break
                self.lexer.add(ch)
                self.nest -= 1
            elif self.expand and ch == "#" and self.lexer.peek() not in "\r\n":
                ch2 = self.lexer.read()

                if ch2 in ["$", "@", "{"]:
                    self.lexer.unread()
                    self.lexer.unread()
                    break
                self.lexer.add(ch)
                self.lexer.unread()
            elif ch == "\\":
                escaped_char = self.lexer.read_escape()
                if (self.is_regexp and len(escaped_char) == 1 and
                    escaped_char[0] in string.printable):
                    self.lexer.add(ch)
                    self.lexer.add(escaped_char[0])
                else:
                    for ch in escaped_char:
                        self.lexer.add(ch)
            elif self.is_qwords and ch.isspace():
                self.lexer.unread()
                break
            elif ch == self.lexer.EOF:
                self.lexer.error()
            else:
                self.lexer.add(ch)
        return self.lexer.emit("STRING_CONTENT")

    def end_found(self):
        if self.is_qwords:
            self.is_end = True
            return self.lexer.emit("LITERAL_SPACE")
        if self.is_regexp:
            flags = ""
            while True:
                ch = self.lexer.read()
                if ch == self.lexer.EOF or not ch.isalpha():
                    self.lexer.unread()
                    break
                elif ch in "ixmouesn":
                    if ch not in flags:
                        flags += ch
                        self.lexer.add(ch)
                else:
                    self.lexer.error()
            return self.lexer.emit("REGEXP_END")
        return self.lexer.emit("STRING_END")


class HeredocTerm(BaseStringTerm):
    def __init__(self, lexer, marker, last_line, indent, expand=True):
        BaseStringTerm.__init__(self, lexer, expand=expand)
        self.marker = marker
        self.last_line = last_line
        self.indent = indent
        self.start_of_line = True

    def next(self):
        if self.is_end:
            if self.last_line:
                # TODO: there should be a real API for this.
                self.lexer.source = self.lexer.source[:self.lexer.idx] + self.last_line + self.lexer.source[self.lexer.idx:]
            return self.lexer.emit("STRING_END")
        if self.start_of_line:
            self.start_of_line = False
            chars = []
            if self.indent:
                while True:
                    ch = self.lexer.read()
                    if ch.isspace():
                        chars.append(ch)
                    else:
                        self.lexer.unread()
                        break
            for c in self.marker:
                ch = self.lexer.read()
                if ch != c:
                    self.lexer.unread()
                    for c in chars:
                        self.lexer.add(c)
                    return self.lexer.emit("STRING_CONTENT")
                chars.append(ch)
            else:
                self.is_end = True
                return self.lexer.emit("STRING_CONTENT")

        ch = self.lexer.read()
        if self.expand and ch == "#":
            self.lexer.add(ch)
            ch = self.lexer.read()
            if ch in ["$", "@"]:
                self.lexer.unread()
                return self.lexer.emit("STRING_DVAR")
            elif ch == "{":
                self.lexer.add(ch)
                return self.lexer.emit("STRING_DBEG")
            else:
                self.lexer.add("#")
        self.lexer.unread()

        while True:
            ch = self.lexer.read()
            if ch in "\r\n":
                self.lexer.newline(ch)
                self.lexer.add("\n")
                self.start_of_line = True
                return self.lexer.emit("STRING_CONTENT")
            elif ch == self.lexer.EOF:
                self.lexer.error()
            elif self.expand and ch == "#" and self.lexer.peek() not in "\r\n":
                ch2 = self.lexer.read()

                if ch2 in ["$", "@", "{"]:
                    self.lexer.unread()
                    self.lexer.unread()
                    return self.lexer.emit("STRING_CONTENT")
                self.lexer.add(ch)
                self.lexer.unread()
            else:
                self.lexer.add(ch)


class StackState(object):
    def __init__(self):
        self._stack = 0

    def begin(self):
        orig = self._stack
        self._stack <<= 1
        self._stack |= 1
        return orig

    def end(self):
        self._stack >>= 1

    def stop(self):
        self._stack <<= 1

    def reset(self, orig):
        self._stack = orig

    def restart(self):
        self._stack |= (self._stack & 1) << 1
        self._stack >>= 1

    def is_in_state(self):
        return (self._stack & 1) != 0
