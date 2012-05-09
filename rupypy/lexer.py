import sys

from pypy.rlib.objectmodel import we_are_translated
from pypy.rlib.parsing.lexer import Token, SourcePos
from pypy.rlib.rstring import StringBuilder
from pypy.rlib.unroll import unrolling_iterable


TOKENS = unrolling_iterable([
    "RETURN",
    "YIELD",
    "IF",
    "UNLESS",
    "THEN",
    "WHILE",
    "DO",
    "BEGIN",
    "RESCUE",
    "ENSURE",
    "DEF",
    "CLASS",
    "MODULE",
    "END",
    "NUMBER",
    "IDENTIFIER",
    "PLUS",
    "MINUS",
    "STAR",
    "DIV",
    "EQ",
    "LT",
    "GT",
    "EXCLAMATION",
    "DOT",
    "DOTDOT",
    "COLON",
    "STRING",
])
for token in TOKENS:
    setattr(sys.modules[__name__], token, token)


class Lexer(object):
    keywords = {
        "return": RETURN,
        "yield": YIELD,
        "if": IF,
        "unless": UNLESS,
        "then": THEN,
        "while": WHILE,
        "do": DO,
        "begin": BEGIN,
        "rescue": RESCUE,
        "ensure": ENSURE,
        "def": DEF,
        "class": CLASS,
        "module": MODULE,
        "end": END,
    }

    def __init__(self, text):
        self.text = text
        self.current_value = []
        self.tokens = []
        self.idx = 0
        self.lineno = 0
        self.columno = 0

    def peek(self):
        return self.text[self.idx + 1]

    def prev(self, back):
        if self.idx - back < 0:
            return None
        return self.text[self.idx - back]

    def add(self, ch):
        self.current_value.append(ch)

    def emit(self, token, value=None):
        if value is None:
            value = "".join(self.current_value)
        self.current_value = []
        pos = SourcePos(self.idx, self.lineno, self.columno)
        self.tokens.append(Token(token, value, pos))

    def tokenize(self):
        state = None

        while self.idx < len(self.text):
            ch = self.text[self.idx]

            if state is None:
                state = self.handle_generic(ch)
            else:
                if we_are_translated():
                    for token in TOKENS:
                        if state == token:
                            state = getattr(self, "handle_" + token)(ch)
                            break
                    else:
                        raise NotImplementedError
                else:
                    state = getattr(self, "handle_" + state)(ch)
            self.idx += 1
        self.finish_token(state)
        self.emit("EOF")
        return self.tokens

    def finish_token(self, state):
        if state == NUMBER:
            self.emit("NUMBER")
        elif state == IDENTIFIER:
            self.emit_identifier()
        elif state is not None:
            assert False

    def emit_identifier(self):
        if "".join(self.current_value) in self.keywords:
            self.emit(self.keywords["".join(self.current_value)])
        else:
            self.emit("IDENTIFIER")

    def handle_generic(self, ch):
        if ch.isdigit():
            self.add(ch)
            return NUMBER
        elif ch.isalpha() or ch == "_":
            self.add(ch)
            return IDENTIFIER
        elif ch == "+":
            self.add(ch)
            return PLUS
        elif ch == "-":
            self.add(ch)
            return MINUS
        elif ch == "*":
            self.add(ch)
            return STAR
        elif ch  == "/":
            self.add(ch)
            self.emit("DIV")
            return None
        elif ch == "<":
            self.add(ch)
            return LT
        elif ch == ">":
            self.add(ch)
            return GT
        elif ch == "!":
            self.add(ch)
            return EXCLAMATION
        elif ch == "(":
            self.add(ch)
            self.emit("LPAREN")
            return None
        elif ch == ")":
            self.add(ch)
            self.emit("RPAREN")
            return None
        elif ch == "[":
            self.add(ch)
            self.emit("LBRACKET")
            return None
        elif ch == "]":
            self.add(ch)
            self.emit("RBRACKET")
            return None
        elif ch == "{":
            self.add(ch)
            self.emit("LBRACE")
            return None
        elif ch == "}":
            self.add(ch)
            self.emit("RBRACE")
            return None
        elif ch == '"':
            return STRING
        elif ch == " ":
            return None
        elif ch == "=":
            self.add(ch)
            return EQ
        elif ch == ".":
            self.add(ch)
            return DOT
        elif ch == ":":
            self.add(ch)
            return COLON
        elif ch == ",":
            self.add(ch)
            self.emit("COMMA")
            return None
        elif ch == "&":
            self.add(ch)
            self.emit("AMP")
            return None
        elif ch == "@":
            self.add(ch)
            self.emit("AT_SIGN")
            return None
        elif ch == "|":
            self.add(ch)
            self.emit("PIPE")
            return None
        elif ch == "\n":
            self.lineno += 1
            self.add(ch)
            self.emit("LINE_END")
            return None
        elif ch == ";":
            self.add(ch)
            self.emit("LINE_END")
            return None
        assert False, ch

    def handle_NUMBER(self, ch):
        if ch == ".":
            if not self.peek().isdigit():
                self.emit("NUMBER")
                return self.handle_generic(ch)
            self.add(ch)
            return NUMBER
        elif ch.isdigit():
            self.add(ch)
            return NUMBER
        else:
            self.emit("NUMBER")
            return self.handle_generic(ch)

    def handle_STRING(self, ch):
        if ch == '"':
            self.emit("STRING")
            return None
        self.add(ch)
        return STRING

    def handle_IDENTIFIER(self, ch):
        if ch.isalnum() or ch == "_":
            self.add(ch)
            return IDENTIFIER
        else:
            self.emit_identifier()
            return self.handle_generic(ch)

    def handle_PLUS(self, ch):
        if ch == "=":
            self.add(ch)
            self.emit("PLUS_EQUAL")
            return None
        self.emit("PLUS")
        return self.handle_generic(ch)

    def handle_MINUS(self, ch):
        if ch.isdigit():
            self.add(ch)
            return NUMBER
        elif ch == " " or self.prev(2) not in ["(", " ", None]:
            self.emit("MINUS")
        else:
            self.emit("UNARY_MINUS")
        return self.handle_generic(ch)

    def handle_STAR(self, ch):
        if ch == " " or self.prev(2) not in ["(", " "]:
            self.emit("MUL")
        else:
            self.emit("UNARY_STAR")
        return self.handle_generic(ch)

    def handle_EQ(self, ch):
        if ch == "=":
            self.add(ch)
            self.emit("EQUAL")
            return None
        elif ch == ">":
            self.add(ch)
            self.emit("ARROW")
            return None
        self.emit("EQ")
        return self.handle_generic(ch)

    def handle_LT(self, ch):
        if ch == "<":
            self.add(ch)
            self.emit("LSHIFT")
            return None
        elif ch == "=":
            self.add(ch)
            self.emit("LE")
            return None
        self.emit("LT")
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
        return self.handle_generic(ch)

    def handle_DOT(self, ch):
        if ch == ".":
            self.add(ch)
            return DOTDOT
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
        else:
            self.emit("COLON")
            return self.handle_generic(ch)
