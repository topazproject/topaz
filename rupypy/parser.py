from rply import ParserGenerator
from rply.token import BaseBox

from rupypy import ast


pg = ParserGenerator(["EOF", "LINE_END", "NUMBER"])


@pg.production("main : suite EOF")
def main(p):
    return p[0]


@pg.production("suite : lines opt_statement opt_line_end")
def suite(p):
    raise NotImplementedError


@pg.production("lines : line lines")
@pg.production("lines :")
def lines(p):
    if p:
        return BoxList([p[0]] + p[1].getlist())
    else:
        return BoxList([])


@pg.production("line : opt_statement LINE_END")
def statement(p):
    return p[0]


@pg.production("opt_line_end : LINE_END")
@pg.production("opt_line_end :")
def opt_line_end(p):
    return None


@pg.production("opt_statement : statement")
@pg.production("opt_statement :")
def opt_statement(p):
    return p[0] if p else None


@pg.production("statement : NUMBER")
def statement_number(p):
    return BoxAST(ast.ConstantInt(int(p[0].getstr())))


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
