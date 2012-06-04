from pypy.rlib.objectmodel import we_are_translated
from pypy.rlib.parsing.lexer import Token, SourcePos
from pypy.rlib.unroll import unrolling_iterable


STATES = unrolling_iterable([
    "NUMBER", "IDENTIFIER", "DOT", "DOTDOT", "PLUS", "MINUS", "STAR", "SLASH",
    "EQ", "EQEQ", "LT", "GT", "LE", "PIPE", "OR", "AMP", "COLON",
    "EXCLAMATION", "QUESTION", "GLOBAL", "SINGLESTRING", "DOUBLESTRING",
    "SYMBOL", "REGEXP", "COMMENT",
])


class LexerError(Exception):
    def __init__(self, pos):
        self.pos = pos


class Keyword(object):
    def __init__(self, normal_token, inline_token, context):
        self.normal_token = normal_token
        self.inline_token = inline_token
        self.context = context


class Lexer(object):
    EXPR_BEG = 0
    EXPR_VALUE = 1
    EXPR_NAME = 2
    EXPR_MID = 3
    EXPR_END = 4
    EXPR_ARG = 5
    EXPR_CLASS = 6
    EXPR_DOT = 7
    EXPR_ENDFN = 8

    keywords = {
        "return": Keyword("RETURN", "RETURN", EXPR_MID),
        "yield": Keyword("YIELD", "YIELD", EXPR_ARG),
        "if": Keyword("IF", "IF_INLINE", EXPR_BEG),
        "unless": Keyword("UNLESS", "UNLESS_INLINE", EXPR_BEG),
        "then": Keyword("THEN", "THEN", EXPR_BEG),
        "elsif": Keyword("ELSIF", "ELSIF", EXPR_BEG),
        "else": Keyword("ELSE", "ELSE", EXPR_BEG),
        "while": Keyword("WHILE", "WHILE", EXPR_BEG),
        "until": Keyword("UNTIL", "UNTIL_INLINE", EXPR_BEG),
        "do": Keyword("DO", "DO", EXPR_BEG),
        "begin": Keyword("BEGIN", "BEGIN", EXPR_BEG),
        "rescue": Keyword("RESCUE", "RESCUE", EXPR_MID),
        "ensure": Keyword("ENSURE", "ENSURE", EXPR_BEG),
        "def": Keyword("DEF", "DEF", EXPR_NAME),
        "class": Keyword("CLASS", "CLASS", EXPR_CLASS),
        "module": Keyword("MODULE", "MODULE", EXPR_BEG),
        "case": Keyword("CASE", "CASE", EXPR_BEG),
        "when": Keyword("WHEN", "WHEN", EXPR_BEG),
        "end": Keyword("END", "END", EXPR_END),
    }

    def __init__(self, text):
        self.text = text
        self.current_value = []
        self.tokens = []
        self.context = self.EXPR_BEG
        self.idx = 0
        self.lineno = 1
        self.columno = 1

    def current_pos(self):
        return SourcePos(self.idx, self.lineno, self.columno)

    def peek(self):
        return self.text[self.idx + 1]

    def prev(self, back):
        if self.idx - back < 0:
            return None
        return self.text[self.idx - back]

    def add(self, ch):
        self.current_value.append(ch)

    def clear(self):
        self.current_value = []

    def emit(self, token, value=None):
        if value is None:
            value = "".join(self.current_value)
        self.clear()
        self.tokens.append(Token(token, value, self.current_pos()))

    def error(self):
        raise LexerError(self.current_pos())

    def tokenize(self):
        state = None

        while self.idx < len(self.text):
            ch = self.text[self.idx]

            if state is None:
                state = self.handle_generic(ch)
            else:
                if we_are_translated():
                    for expected_state in STATES:
                        if state == expected_state:
                            state = getattr(self, "handle_" + expected_state)(ch)
                            break
                    else:
                        raise NotImplementedError
                else:
                    assert state in STATES
                    state = getattr(self, "handle_" + state)(ch)
            self.idx += 1
            self.columno += 1
        self.finish_token(state)
        self.emit("EOF")
        return self.tokens

    def finish_token(self, state):
        if state == "NUMBER":
            self.emit("NUMBER")
        elif state == "IDENTIFIER":
            self.emit_identifier()
        elif state == "SYMBOL":
            self.emit("SYMBOL")
        elif state == "GLOBAL":
            self.emit("GLOBAL")
        elif state is not None:
            assert False

    def emit_identifier(self):
        value = "".join(self.current_value)
        context = self.context
        if value in self.keywords and self.context != self.EXPR_DOT:
            keyword = self.keywords[value]
            self.context = keyword.context

            if context in [self.EXPR_BEG, self.EXPR_VALUE]:
                self.emit(keyword.normal_token)
            else:
                self.emit(keyword.inline_token)
                self.context = self.EXPR_BEG
        else:
            self.emit("IDENTIFIER")
            if self.context in [
                self.EXPR_BEG, self.EXPR_MID, self.EXPR_VALUE, self.EXPR_CLASS,
                self.EXPR_ARG, self.EXPR_DOT
            ]:
                self.context = self.EXPR_ARG
            elif self.context == self.EXPR_NAME:
                self.context = self.EXPR_ENDFN
            else:
                self.context = self.EXPR_END

    def handle_generic(self, ch):
        if ch.isdigit():
            self.add(ch)
            return "NUMBER"
        elif ch.isalpha() or ch == "_":
            self.add(ch)
            return "IDENTIFIER"
        elif ch == "+":
            self.add(ch)
            return "PLUS"
        elif ch == "-":
            self.add(ch)
            return "MINUS"
        elif ch == "*":
            self.add(ch)
            return "STAR"
        elif ch == "/":
            self.add(ch)
            return "SLASH"
        elif ch == "<":
            self.add(ch)
            return "LT"
        elif ch == ">":
            self.add(ch)
            return "GT"
        elif ch == "!":
            self.add(ch)
            return "EXCLAMATION"
        elif ch == "(":
            self.add(ch)
            self.emit("LPAREN")
            self.context = self.EXPR_BEG
            return None
        elif ch == ")":
            self.add(ch)
            self.emit("RPAREN")
            self.context = self.EXPR_ENDFN
            return None
        elif ch == "[":
            self.add(ch)
            if (self.context not in [self.EXPR_END, self.EXPR_ENDFN] and
                (self.prev(1) is None or not self.prev(1)[0].isalnum())):
                self.emit("LBRACKET")
                self.context = self.EXPR_BEG
            else:
                self.emit("LSUBSCRIPT")
                self.context = self.EXPR_BEG
            return None
        elif ch == "]":
            self.add(ch)
            self.emit("RBRACKET")
            self.context = self.EXPR_END
            return None
        elif ch == "{":
            self.add(ch)
            self.emit("LBRACE")
            return None
        elif ch == "}":
            self.add(ch)
            self.emit("RBRACE")
            self.context = self.EXPR_ENDFN
            return None
        elif ch == '"':
            return "DOUBLESTRING"
        elif ch == "'":
            return "SINGLESTRING"
        elif ch == " ":
            return None
        elif ch == "=":
            self.add(ch)
            return "EQ"
        elif ch == ".":
            self.add(ch)
            return "DOT"
        elif ch == ":":
            self.add(ch)
            return "COLON"
        elif ch == "?":
            self.add(ch)
            if self.context in [self.EXPR_END, self.EXPR_ENDFN]:
                self.emit("QUESTION")
                self.context = self.EXPR_VALUE
                return None
            else:
                return "QUESTION"
        elif ch == ",":
            self.add(ch)
            self.emit("COMMA")
            self.context = self.EXPR_BEG
            return None
        elif ch == "&":
            self.add(ch)
            return "AMP"
        elif ch == "@":
            self.add(ch)
            self.emit("AT_SIGN")
            return None
        elif ch == "$":
            self.add(ch)
            return "GLOBAL"
        elif ch == "|":
            self.add(ch)
            return "PIPE"
        elif ch == "%":
            self.add(ch)
            self.emit("MODULO")
            return None
        elif ch == "\n":
            if self.context != self.EXPR_BEG:
                self.add(ch)
                self.emit("LINE_END")
            self.lineno += 1
            self.columno = 0
            self.context = self.EXPR_BEG
            return None
        elif ch == ";":
            self.add(ch)
            self.emit("LINE_END")
            return None
        elif ch == "#":
            return "COMMENT"
        assert False, ch

    def handle_NUMBER(self, ch):
        self.context = self.EXPR_END
        if ch in "xXbBdDoO" and self.current_value == ["0"]:
            if ch == "x" or ch == "X":
                self.add("X")
            elif ch == "b" or ch == "B":
                self.add("B")
            elif ch == "o" or ch == "O":
                self.add("O")
            return "NUMBER"
        if ch == ".":
            if not self.peek().isdigit():
                self.emit("NUMBER")
                return self.handle_generic(ch)
            self.add(ch)
            return "NUMBER"
        elif ch.isdigit() or ("X" in self.current_value and ch in "abcdefABCDEF"):
            self.add(ch)
            return "NUMBER"
        elif ch == "_":
            if not self.peek().isdigit():
                self.error()
            return "NUMBER"
        elif ch == "E" or ch == "e":
            if not self.peek().isdigit():
                self.error()
            self.add("E")
            return "NUMBER"
        else:
            self.emit("NUMBER")
            return self.handle_generic(ch)

    def handle_DOUBLESTRING(self, ch):
        self.context = self.EXPR_END
        if ch == '"':
            self.emit("STRING")
            return None
        self.add(ch)
        return "DOUBLESTRING"

    def handle_SINGLESTRING(self, ch):
        self.context = self.EXPR_END
        if ch == "'":
            self.emit("STRING")
            return None
        self.add(ch)
        return "SINGLESTRING"

    def handle_IDENTIFIER(self, ch):
        if ch in "!?":
            self.add(ch)
            self.emit_identifier()
            return None
        elif ch.isalnum() or ch == "_":
            self.add(ch)
            return "IDENTIFIER"
        else:
            self.emit_identifier()
            return self.handle_generic(ch)

    def handle_SYMBOL(self, ch):
        self.context = self.EXPR_END
        if not (ch.isalnum() or ch == "_"):
            self.emit("SYMBOL")
            return self.handle_generic(ch)
        self.add(ch)
        return "SYMBOL"

    def handle_PLUS(self, ch):
        if ch == "=":
            self.add(ch)
            self.emit("PLUS_EQUAL")
            return None
        self.emit("PLUS")
        self.context = self.EXPR_BEG
        return self.handle_generic(ch)

    def handle_MINUS(self, ch):
        if ch.isdigit():
            self.add(ch)
            return "NUMBER"
        elif ch == "=":
            self.add(ch)
            self.emit("MINUS_EQUAL")
            return None
        elif ch == " " or self.prev(2) not in ["(", " ", None]:
            self.emit("MINUS")
        else:
            self.emit("UNARY_MINUS")
        return self.handle_generic(ch)

    def handle_STAR(self, ch):
        if ch == " " or self.prev(2) not in ["(", "|", " "]:
            self.emit("MUL")
        else:
            self.emit("UNARY_STAR")
        return self.handle_generic(ch)

    def handle_SLASH(self, ch):
        if self.context in [self.EXPR_BEG, self.EXPR_VALUE]:
            self.clear()
            self.add(ch)
            return "REGEXP"
        elif ch == "=":
            self.emit("DIV_EQUAL")
            return None
        self.emit("DIV")
        return self.handle_generic(ch)

    def handle_EQ(self, ch):
        if ch == "=":
            self.add(ch)
            return "EQEQ"
        elif ch == ">":
            self.add(ch)
            self.emit("ARROW")
            return None
        elif ch == "~":
            self.add(ch)
            self.emit("EQUAL_TILDE")
            return None
        self.context = self.EXPR_BEG
        self.emit("EQ")
        return self.handle_generic(ch)

    def handle_EQEQ(self, ch):
        if ch == "=":
            self.add(ch)
            self.emit("EQEQEQ")
            return None
        self.emit("EQEQ")
        return self.handle_generic(ch)

    def handle_LT(self, ch):
        if ch == "<":
            self.add(ch)
            self.emit("LSHIFT")
            self.context = self.EXPR_BEG
            return None
        elif ch == "=":
            self.add(ch)
            return "LE"
        self.emit("LT")
        return self.handle_generic(ch)

    def handle_LE(self, ch):
        if ch == ">":
            self.add(ch)
            self.emit("LEGT")
            return None
        self.emit("LE")
        return self.handle_generic(ch)

    def handle_GT(self, ch):
        if ch == "=":
            self.add(ch)
            self.emit("GE")
            return None
        self.emit("GT")
        return self.handle_generic(ch)

    def handle_EXCLAMATION(self, ch):
        if ch == "=":
            self.add(ch)
            self.emit("NE")
            return None
        elif ch == "~":
            self.add(ch)
            self.emit("EXCLAMATION_TILDE")
            return None
        self.emit("EXCLAMATION")
        return self.handle_generic(ch)

    def handle_DOT(self, ch):
        if ch == ".":
            self.add(ch)
            return "DOTDOT"
        self.context = self.EXPR_DOT
        self.emit("DOT")
        return self.handle_generic(ch)

    def handle_DOTDOT(self, ch):
        if ch == ".":
            self.add(ch)
            self.emit("DOTDOTDOT")
            return None
        self.emit("DOTDOT")
        return self.handle_generic(ch)

    def handle_COLON(self, ch):
        if ch == ":":
            self.add(ch)
            self.emit("COLONCOLON")
            return None
        elif self.context == self.EXPR_END or ch == " " or not (ch.isalnum() or ch == "_"):
            self.emit("COLON")
            self.context = self.EXPR_BEG
            return self.handle_generic(ch)
        else:
            self.clear()
            self.add(ch)
            return "SYMBOL"

    def handle_AMP(self, ch):
        if ch == "&":
            self.add(ch)
            self.emit("AND")
            self.context = self.EXPR_BEG
            return None
        self.emit("AMP")
        return self.handle_generic(ch)

    def handle_COMMENT(self, ch):
        if ch == "\n":
            return self.handle_generic(ch)
        return "COMMENT"

    def handle_PIPE(self, ch):
        if ch == "|":
            self.add(ch)
            return "OR"
        self.emit("PIPE")
        if self.context == self.EXPR_NAME:
            self.context = self.EXPR_ARG
        else:
            self.context = self.EXPR_BEG
        return self.handle_generic(ch)

    def handle_OR(self, ch):
        if ch == "=":
            self.add(ch)
            self.emit("OR_EQUAL")
            return None
        self.emit("OR")
        return self.handle_generic(ch)

    def handle_GLOBAL(self, ch):
        self.context = self.EXPR_END
        if ch in ">:":
            self.add(ch)
            self.emit("GLOBAL")
            return None
        elif not (ch.isalnum() or ch == "_"):
            self.emit("GLOBAL")
            return self.handle_generic(ch)
        self.add(ch)
        return "GLOBAL"

    def handle_QUESTION(self, ch):
        if ch == " ":
            self.emit("QUESTION")
            self.context = self.EXPR_VALUE
            return self.handle_generic(ch)
        self.clear()
        self.add(ch)
        self.emit("STRING")
        self.context = self.EXPR_END
        return None

    def handle_REGEXP(self, ch):
        self.context = self.EXPR_END
        if ch == "/":
            self.emit("REGEXP")
            return None
        self.add(ch)
        return "REGEXP"
