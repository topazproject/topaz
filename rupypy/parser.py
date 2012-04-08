import os

from pypy.rlib.parsing.ebnfparse import parse_ebnf, make_parse_function

from rupypy.ast import (Block, Statement, Assignment, BinOp, Send, Self,
    Variable, ConstantInt)


with open(os.path.join(os.path.dirname(__file__), "grammar.txt")) as f:
    grammar = f.read()
regexs, rules, _ = parse_ebnf(grammar)
_parse = make_parse_function(regexs, rules, eof=True)


class Transformer(object):
    def visit_main(self, node):
        return self.visit_block(node.children[0])

    def visit_block(self, node):
        stmts = []
        stmts.append(self.visit_stmt(node.children[0]))
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
        elif symname == "assignment":
            return self.visit_assignment(node)
        raise NotImplementedError(symname)

    def visit_assignment(self, node):
        return Assignment(
            Variable(node.children[0].children[0].additional_info),
            self.visit_expr(node.children[2].children[0]),
        )


    def visit_arg(self, node):
        symname = node.symbol
        if symname in ["additive", "multitive"]:
            return self.visit_subexpr(node)
        elif symname == "primary":
            return self.visit_primary(node)
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
        if len(node.children) == 1:
            symname = node.children[0].symbol
            if symname == "literal":
                return self.visit_literal(node.children[0])
            elif symname == "send":
                return self.visit_send(node.children[0])
            elif symname == "IDENTIFIER":
                return Variable(node.children[0].additional_info)
        elif node.children[0].additional_info == "(":
            return self.visit_expr(node.children[1])
        raise NotImplementedError(node.symbol)

    def visit_send(self, node):
        method = node.children[0].children[0].additional_info
        args = []
        node = node.children[1].children[0]
        while True:
            args.append(self.visit_expr(node.children[0]))
            if len(node.children) == 1:
                break
            node = node.children[2]
        return Send(Self(), method, args)

    def visit_literal(self, node):
        symname = node.children[0].symbol
        if symname == "INTEGER":
            return ConstantInt(int(node.children[0].additional_info))
        raise NotImplementedError
