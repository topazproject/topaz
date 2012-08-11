from rply import ParserGenerator
from rply.token import BaseBox

from rupypy import ast


pg = ParserGenerator(["EOF", "LINE_END", "NUMBER"])


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


@pg.production("stmt : NUMBER")
def stmt(p):
    s = p[0].getstr()
    if "." in s:
        node = ast.ConstantFloat(float(s))
    else:
        node = ast.ConstantInt(int(s))
    return BoxAST(node)


parser = pg.build()


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
