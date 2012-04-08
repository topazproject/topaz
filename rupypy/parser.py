import os

from pypy.rlib.parsing.ebnfparse import parse_ebnf, make_parse_function

from rupypy.ast import Block, Statement, BinOp, ConstantInt


with open(os.path.join(os.path.dirname(__file__), "grammar.txt")) as f:
    grammar = f.read()
regexs, rules, _ = parse_ebnf(grammar)
_parse = make_parse_function(regexs, rules, eof=True)


class Transformer(object):
    def visit_main(self, node):
        return self.visit_block(node.children[0])

    def visit_block(self, node):
        stmts = []
        while True:
            stmts.append(self.visit_stmt(node.children[0]))
            if len(node.children) == 1:
                break
            node = node.children[1]
        return Block(stmts)

    def visit_stmt(self, node):
        if node.children[0].symbol == "expr":
            return Statement(self.visit_expr(node.children[0]))
        raise NotImplementedError

    def visit_expr(self, node):
        if node.symbol == "expr":
            node = node.children[0]
        symname = node.symbol
        if symname == "arg":
            return self.visit_arg(node.children[0])
        raise NotImplementedError(symname)

    def visit_arg(self, node):
        symname = node.symbol
        if symname in ["additive", "multitive"]:
            return self.visit_subexpr(node)
        elif symname == "primary":
            return self.visit_primary(node.children[0])
        raise NotImplementedError(symname)

    def visit_subexpr(self, node):
        if len(node.children) == 1:
            return self.visit_arg(node.children[0])
        return BinOp(
            node.children[1].additional_info,
            self.visit_arg(node.children[0]),
            self.visit_arg(node.children[2]),
        )
        import py
        py.test.set_trace()

    def visit_primary(self, node):
        symname = node.symbol
        if symname == "literal":
            return self.visit_literal(node.children[0])
        raise NotImplementedError

    def visit_literal(self, node):
        symname = node.symbol
        if symname == "INTEGER":
            return ConstantInt(int(node.additional_info))
        raise NotImplementedError
