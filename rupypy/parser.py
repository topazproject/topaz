import os

from pypy.rlib.parsing.ebnfparse import parse_ebnf, make_parse_function

from rupypy.ast import (Main, Block, Statement, Assignment, If, While, Function,
    Return, BinOp, Send, Self, Variable, Array, ConstantInt, ConstantString)


with open(os.path.join(os.path.dirname(__file__), "grammar.txt")) as f:
    grammar = f.read()
regexs, rules, to_ast = parse_ebnf(grammar)
_parse = make_parse_function(regexs, rules, eof=True)


class Transformer(object):
    def visit_main(self, node):
        return Main(self.visit_block(node))

    def visit_block(self, node, start_idx=0, end_idx=-1):
        if end_idx == -1:
            end_idx = len(node.children)
        stmts = []

        assert end_idx >= 0
        for node in node.children[start_idx:end_idx]:
            if node.symbol == "line":
                if not node.children:
                    continue
                node = node.children[0]
            stmts.append(self.visit_stmt(node))
        return Block(stmts)

    def visit_stmt(self, node):
        if len(node.children) == 2:
            return Return(self.visit_expr(node.children[1]))
        return Statement(self.visit_expr(node.children[0]))

    def visit_expr(self, node):
        if node.children[0].symbol == "assignment":
            return self.visit_assignment(node.children[0])
        return self.visit_arg(node.children[0])

    def visit_assignment(self, node):
        return Assignment(
            node.children[0].children[0].additional_info,
            self.visit_expr(node.children[2].children[0]),
        )

    def visit_arg(self, node):
        if node.symbol == "arg":
            node = node.children[0]

        symname = node.symbol
        if symname in ["comparison", "shiftive", "additive", "multitive"]:
            return self.visit_subexpr(node)
        elif symname == "send":
            return self.visit_send(node)
        elif symname == "primary":
            return self.visit_primary(node)
        raise NotImplementedError(symname)

    def visit_subexpr(self, node):
        return BinOp(
            node.children[1].additional_info,
            self.visit_arg(node.children[0]),
            self.visit_arg(node.children[2]),
        )

    def visit_send(self, node):
        if node.children[0].symbol != "primary":
            return Send(
                Self(),
                node.children[0].children[0].additional_info,
                self.visit_send_args(node.children[1])
            )

        target = self.visit_primary(node.children[0])
        for trailer in node.children[1].children:
            node = trailer.children[0]
            if node.symbol == "attribute":
                method = node.children[0].children[0].additional_info
                if len(node.children) == 1:
                    args = []
                else:
                    args = self.visit_send_args(node.children[1])
            elif node.symbol == "subscript":
                args = [self.visit_arg(node.children[0])]
                method = "[]"
            else:
                raise NotImplementedError
            target = Send(
                target,
                method,
                args,
            )
        return target

    def visit_send_args(self, node):
        return [self.visit_arg(n) for n in node.children[0].children]

    def visit_primary(self, node):
        if len(node.children) == 1:
            symname = node.children[0].symbol
            if symname == "literal":
                return self.visit_literal(node.children[0])
            elif symname == "IDENTIFIER":
                return Variable(node.children[0].additional_info)
        elif node.children[0].additional_info == "(":
            return self.visit_expr(node.children[1])
        elif node.children[0].additional_info == "[":
            return self.visit_array(node.children[1])
        elif node.children[0].additional_info == "if":
            return self.visit_if(node)
        elif node.children[0].additional_info == "while":
            return self.visit_while(node)
        elif node.children[0].additional_info == "def":
            return self.visit_def(node)
        raise NotImplementedError(node.symbol)

    def visit_array(self, node):
        return Array([
            self.visit_arg(n) for n in node.children
        ])

    def visit_literal(self, node):
        symname = node.children[0].symbol
        if symname == "INTEGER":
            return self.visit_integer(node.children[0])
        elif symname == "STRING":
            return self.visit_string(node.children[0])
        raise NotImplementedError(symname)

    def visit_if(self, node):
        return If(
            self.visit_expr(node.children[1]),
            self.visit_block(node, start_idx=3, end_idx=len(node.children) - 1),
        )

    def visit_while(self, node):
        return While(
            self.visit_expr(node.children[1]),
            self.visit_block(node, start_idx=3, end_idx=len(node.children) - 1),
        )

    def visit_def(self, node):
        return Function(
            node.children[1].additional_info,
            self.visit_argdecl(node.children[2]),
            self.visit_block(node, start_idx=3, end_idx=len(node.children) - 1),
        )

    def visit_argdecl(self, node):
        if not node.children:
            return []
        return [n.additional_info for n in node.children[0].children]

    def visit_integer(self, node):
        return ConstantInt(int(node.additional_info))

    def visit_string(self, node):
        return ConstantString(node.additional_info[1:-1])
