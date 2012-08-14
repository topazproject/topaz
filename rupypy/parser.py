from rply import ParserGenerator
from rply.token import BaseBox

from rupypy import ast


class LexerWrapper(object):
    def __init__(self, lexer):
        self.lexer = lexer
        self.token_iter = iter(lexer)

    def next(self):
        try:
            return self.token_iter.next()
        except StopIteration:
            return None


class BoxAST(BaseBox):
    def __init__(self, node):
        BaseBox.__init__(self)
        self.node = node

    def getast(self):
        return self.node


class BoxASTList(BaseBox):
    def __init__(self, nodes):
        BaseBox.__init__(self)
        self.nodes = nodes

    def getlist(self):
        return self.nodes


pg = ParserGenerator([
    "EOF", "LINE_END", "NUMBER", "IDENTIFIER", "GLOBAL", "LBRACKET",
    "LSUBSCRIPT", "RBRACKET", "COMMA", "EXCLAMATION", "AND_LITERAL",
    "OR_LITERAL", "NOT_LITERAL", "PLUS", "MUL", "DIV", "MODULO", "LSHIFT",
    "RSHIFT", "AMP", "PIPE", "AND", "OR", "EQEQ", "NE", "EQEQEQ", "LT", "LE",
    "GT", "GE", "LEGT", "EQUAL_TILDE", "EXCLAMATION_TILDE", "SSTRING",
    "REGEXP_BEGIN", "REGEXP_END", "STRING_BEGIN", "STRING_END", "STRING_VALUE",
    "DSTRING_START", "DSTRING_END",
], precedence=[
    ("nonassoc", ["LOWEST"]),
    ("left", ["OR_LITERAL", "AND_LITERAL"]),
    ("right", ["NOT_LITERAL"]),
    ("left", ["OR"]),
    ("left", ["AND"]),
    ("nonassoc", ["LEGT", "EQ", "EQEQ", "NE", "EQUAL_TILDE", "EXCLAMATION_TILDE"]),
    ("left", ["GT", "GE", "LT", "LE"]),
    ("left", ["PIPE", "CARET"]),
    ("left", ["AMP"]),
    ("left", ["LSHIFT", "RSHIFT"]),
    ("left", ["PLUS", "MINUS"]),
    ("left", ["MUL", "DIV", "MOD"]),
    ("right", ["UMINUS"]),
    ("right", ["POW"]),
    ("right", ["EXCLAMATION", "TILDE", "UPLUS"]),
])


@pg.production("main : suite EOF")
def main(p):
    return BoxAST(ast.Main(p[0].getast()))


@pg.production("suite : stmts opt_line_ends")
def suite(p):
    return BoxAST(ast.Block(p[0].getlist()))


@pg.production("stmts : none")
def stmts_none(p):
    return BoxASTList([])


@pg.production("stmts : stmt")
def stmts_stmt(p):
    return BoxASTList([p[0].getast()])


@pg.production("stmts : stmts line_ends stmt")
def stmts_stmts(p):
    return BoxASTList(p[0].getlist() + [p[2].getast()])


@pg.production("line_ends : line_ends LINE_END")
@pg.production("line_ends : LINE_END")
def line_ends(p):
    return None


@pg.production("opt_line_ends : none")
@pg.production("opt_line_ends : line_ends")
def opt_line_ends(p):
    return None


@pg.production("none :")
def none(p):
    return None


@pg.production("stmt : expr")
def stmt(p):
    return BoxAST(ast.Statement(p[0].getast()))


@pg.production("expr : expr OR_LITERAL expr")
def expr_or(p):
    return BoxAST(ast.Or(p[0].getast(), p[2].getast()))


@pg.production("expr : expr AND_LITERAL expr")
def expr_and(p):
    return BoxAST(ast.And(p[0].getast(), p[2].getast()))


@pg.production("expr : NOT_LITERAL expr")
def expr_not(p):
    return BoxAST(ast.Not(p[1].getast()))


@pg.production("expr : arg")
def expr_arg(p):
    return p[0]


@pg.production("arg : arg PLUS arg")
@pg.production("arg : arg MUL arg")
@pg.production("arg : arg DIV arg")
@pg.production("arg : arg MODULO arg")
@pg.production("arg : arg EQEQ arg")
@pg.production("arg : arg NE arg")
@pg.production("arg : arg EQEQEQ arg")
@pg.production("arg : arg LT arg")
@pg.production("arg : arg LE arg")
@pg.production("arg : arg GT arg")
@pg.production("arg : arg GE arg")
@pg.production("arg : arg LEGT arg")
@pg.production("arg : arg EQUAL_TILDE arg")
@pg.production("arg : arg LSHIFT arg")
@pg.production("arg : arg RSHIFT arg")
@pg.production("arg : arg PIPE arg")
@pg.production("arg : arg AMP arg")
def arg_binop(p):
    node = ast.BinOp(
        p[1].getstr(),
        p[0].getast(),
        p[2].getast(),
        p[1].getsourcepos().lineno
    )
    return BoxAST(node)


@pg.production("arg : arg EXCLAMATION_TILDE arg")
def arg_exclamation_tilde(p):
    node = ast.Not(ast.BinOp(
        "=~",
        p[0].getast(),
        p[2].getast(),
        p[1].getsourcepos().lineno
    ))
    return BoxAST(node)


@pg.production("arg : arg AND arg")
def arg_and(p):
    node = ast.And(p[0].getast(), p[2].getast())
    return BoxAST(node)


@pg.production("arg : arg OR arg")
def arg_or(p):
    node = ast.Or(p[0].getast(), p[2].getast())
    return BoxAST(node)


@pg.production("arg : EXCLAMATION arg")
def arg_exclamation(p):
    return BoxAST(ast.Not(p[1].getast()))


@pg.production("arg : IDENTIFIER args")
def arg_call(p):
    node = ast.Send(
        ast.Self(p[0].getsourcepos().lineno),
        p[0].getstr(),
        p[1].getlist(),
        None,
        p[0].getsourcepos().lineno
    )
    return BoxAST(node)


@pg.production("arg : arg LSUBSCRIPT args RBRACKET")
def arg_subscript(p):
    node = ast.Subscript(
        p[0].getast(),
        p[2].getlist(),
        p[1].getsourcepos().lineno,
    )
    return BoxAST(node)


@pg.production("arg : primary")
def arg_primary(p):
    return p[0]


@pg.production("args : args arg")
def args(p):
    return BoxASTList(p[0].getlist() + [p[1].getast()])


@pg.production("args : none")
def args_empty(p):
    return BoxASTList([])


@pg.production("primary : LBRACKET args opt_array_trailer RBRACKET")
def primary_array(p):
    return BoxAST(ast.Array(p[1].getlist()))


@pg.production("opt_array_trailer : COMMA")
@pg.production("opt_array_trailer : LINE_END")
@pg.production("opt_array_trailer : none")
def opt_array_trailer(p):
    return None


@pg.production("primary : NUMBER")
def primary_number(p):
    s = p[0].getstr()
    if "." in s or "E" in s:
        node = ast.ConstantFloat(float(s))
    elif "X" in s:
        node = ast.ConstantInt(int(s[2:], 16))
    elif "O" in s:
        node = ast.ConstantInt(int(s[2:], 8))
    elif "B" in s:
        node = ast.ConstantInt(int(s[2:], 2))
    else:
        node = ast.ConstantInt(int(s))
    return BoxAST(node)


@pg.production("primary : regexp")
def primary_regexp(p):
    return p[0]


@pg.production("primary : variable")
def primary_variable(p):
    return p[0]


@pg.production("primary : SSTRING")
def primary_sstring(p):
    return BoxAST(ast.ConstantString(p[0].getstr()))


@pg.production("variable : IDENTIFIER")
def variable_identifier(p):
    return BoxAST(ast.Variable(p[0].getstr(), p[0].getsourcepos().lineno))


@pg.production("variable : GLOBAL")
def variable_global(p):
    return BoxAST(ast.Global(p[0].getstr()))


@pg.production("regexp : REGEXP_BEGIN string REGEXP_END")
def regexp(p):
    s = ""
    for node in p[1].getlist():
        if not isinstance(node, ast.ConstantString):
            break
        s += node.strvalue
    else:
        return BoxAST(ast.ConstantRegexp(s))
    return BoxAST(ast.DynamicRegexp(p[1].getlist()))


@pg.production("string : STRING_BEGIN string_contents STRING_END")
def string(p):
    return p[1]


@pg.production("string_contents : string_contents string_content")
def string_contents(p):
    return BoxASTList(p[0].getlist() + [p[1].getast()])


@pg.production("string_contents : none")
def string_contents_empty(p):
    return BoxASTList([])


@pg.production("string_content : STRING_VALUE")
def string_content(p):
    return BoxAST(ast.ConstantString(p[0].getstr()))


@pg.production("string_content : DSTRING_START stmt DSTRING_END")
def string_content_dstring(p):
    return BoxAST(p[1].getast())


parser = pg.build()
