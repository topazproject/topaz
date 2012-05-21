from pypy.rlib.objectmodel import we_are_translated
from pypy.rlib.parsing.lexer import Token, SourcePos
from pypy.rlib.unroll import unrolling_iterable


STATES = unrolling_iterable([
    "NUMBER", "IDENTIFIER", "DOT", "DOTDOT", "PLUS", "MINUS", "STAR", "EQ",
    "EQEQ", "LT", "GT", "PIPE", "AMP", "COLON", "EXCLAMATION", "SINGLESTRING",
    "DOUBLESTRING", "COMMENT",
])


class LexerError(Exception):
    def __init__(self, pos):
        self.pos = pos


class Lexer(object):
    keywords = {
        "return": ["RETURN"],
        "yield": ["YIELD"],
        "if": ["IF", "IF_INLINE"],
        "unless": ["UNLESS", "UNLESS_INLINE"],
        "then": ["THEN"],
        "elsif": ["ELSIF"],
        "else": ["ELSE"],
        "while": ["WHILE"],
        "until": ["UNTIL", "UNTIL_INLINE"],
        "do": ["DO"],
        "begin": ["BEGIN"],
        "rescue": ["RESCUE"],
        "ensure": ["ENSURE"],
        "def": ["DEF"],
        "class": ["CLASS"],
        "module": ["MODULE"],
        "end": ["END"],
    }
    EXPR_BEG = 0
    EXPR_VALUE = 1
    EXPR_NAME = 2

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

    def emit(self, token, value=None):
        if value is None:
            value = "".join(self.current_value)
        self.current_value = []
        self.tokens.append(Token(token, value, self.current_pos()))

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
        elif state is not None:
            assert False

    def emit_identifier(self):
        value = "".join(self.current_value)
        name = True
        if value in self.keywords:
            tokens = self.keywords[value]
            if len(tokens) == 2:
                [normal, inline] = tokens
                name = False
            else:
                [normal] = [inline] = tokens

            if self.context in [self.EXPR_BEG, self.EXPR_VALUE]:
                self.emit(normal)
            else:
                self.emit(inline)
        else:
            self.emit("IDENTIFIER")
        if name:
            self.context = self.EXPR_NAME
        else:
            self.context = self.EXPR_NAME

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
            self.emit("DIV")
            return None
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
            self.emit("QUESTION")
            return None
        elif ch == ",":
            self.add(ch)
            self.emit("COMMA")
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
            self.emit("DOLLAR")
            return None
        elif ch == "|":
            self.add(ch)
            return "PIPE"
        elif ch == "\n":
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
        if ch == ".":
            if not self.peek().isdigit():
                self.emit("NUMBER")
                return self.handle_generic(ch)
            self.add(ch)
            return "NUMBER"
        elif ch.isdigit():
            self.add(ch)
            return "NUMBER"
        else:
            self.emit("NUMBER")
            return self.handle_generic(ch)

    def handle_DOUBLESTRING(self, ch):
        if ch == '"':
            self.emit("STRING")
            return None
        self.add(ch)
        return "DOUBLESTRING"

    def handle_SINGLESTRING(self, ch):
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
        if ch == " " or self.prev(2) not in ["(", " "]:
            self.emit("MUL")
        else:
            self.emit("UNARY_STAR")
        return self.handle_generic(ch)

    def handle_EQ(self, ch):
        if ch == "=":
            self.add(ch)
            return "EQEQ"
        elif ch == ">":
            self.add(ch)
            self.emit("ARROW")
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
        self.emit("EXCLAMATION")
        return self.handle_generic(ch)

    def handle_DOT(self, ch):
        if ch == ".":
            self.add(ch)
            return "DOTDOT"
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

    def handle_AMP(self, ch):
        if ch == "&":
            self.add(ch)
            self.emit("AND")
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
            self.emit("OR")
            return None
        self.emit("PIPE")
        return self.handle_generic(ch)
