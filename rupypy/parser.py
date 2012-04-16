import os

from pypy.rlib.parsing.ebnfparse import parse_ebnf, make_parse_function

from rupypy.ast import (Main, Block, Statement, Assignment,
    InstanceVariableAssignment, If, While, Class, Function, Return, Yield,
    BinOp, Send, SendBlock, Self, Variable, InstanceVariable, Array,
    ConstantInt, ConstantString)


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
        elif len(node.children) == 1 and node.children[0].symbol == "block":
            return Statement(self.visit_send_block(node.children[0]))
        return Statement(self.visit_expr(node.children[0]))

    def visit_send_block(self, node):
        send = self.visit_real_send(node.children[0])
        assert isinstance(send, Send)
        block_args = []
        start_idx = 2
        if node.children[2].symbol == "arglist":
            block_args = self.visit_arglist(node.children[2])
            start_idx += 1
        block = self.visit_block(node, start_idx=start_idx, end_idx=len(node.children) - 1)
        return SendBlock(
            send.receiver,
            send.method,
            send.args,
            block_args,
            block,
        )

    def visit_expr(self, node):
        if node.children[0].symbol == "assignment":
            return self.visit_assignment(node.children[0])
        elif node.children[0].symbol == "yield":
            return self.visit_yield(node.children[0])
        return self.visit_arg(node.children[0])

    def visit_assignment(self, node):
        target = node.children[0].children[0]
        value = self.visit_expr(node.children[2].children[0])
        if len(target.children) == 1:
            return Assignment(target.children[0].additional_info, value)
        else:
            return InstanceVariableAssignment(
                target.children[1].additional_info, value
            )

    def visit_yield(self, node):
        args = []
        if node.children:
            args = self.visit_send_args(node)
        return Yield(args)

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
        if node.children[0].symbol == "real_send":
            return self.visit_real_send(node.children[0])
        raise NotImplementedError

    def visit_real_send(self, node):
        if node.children[0].symbol != "primary":
            return Send(
                Self(),
                node.children[0].additional_info,
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
            elif symname == "varname":
                return self.visit_varname(node.children[0])
        elif node.children[0].additional_info == "(":
            return self.visit_expr(node.children[1])
        elif node.children[0].additional_info == "[":
            return self.visit_array(node)
        elif node.children[0].additional_info == "if":
            return self.visit_if(node)
        elif node.children[0].additional_info == "while":
            return self.visit_while(node)
        elif node.children[0].additional_info == "def":
            return self.visit_def(node)
        elif node.children[0].additional_info == "class":
            return self.visit_class(node)
        raise NotImplementedError(node.symbol)

    def visit_array(self, node):
        if len(node.children) == 3:
            items = [
                self.visit_arg(n) for n in node.children[1].children
            ]
        else:
            items = []
        return Array(items)

    def visit_literal(self, node):
        symname = node.children[0].symbol
        if symname == "INTEGER":
            return self.visit_integer(node.children[0])
        elif symname == "STRING":
            return self.visit_string(node.children[0])
        raise NotImplementedError(symname)

    def visit_varname(self, node):
        if len(node.children) == 1:
            return Variable(node.children[0].additional_info)
        else:
            return InstanceVariable(node.children[1].additional_info)

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

    def visit_class(self, node):
        return Class(
            node.children[1].additional_info,
            None,
            self.visit_block(node, start_idx=2, end_idx=len(node.children) - 1),
        )

    def visit_argdecl(self, node):
        if not node.children:
            return []
        return self.visit_arglist(node.children[0])

    def visit_arglist(self, node):
        return [n.additional_info for n in node.children]

    def visit_integer(self, node):
        return ConstantInt(int(node.additional_info))

    def visit_string(self, node):
        end = len(node.additional_info) - 1
        assert end >= 0
        return ConstantString(node.additional_info[1:end])
