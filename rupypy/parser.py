import os

from pypy.rlib.parsing.ebnfparse import parse_ebnf, make_parse_function

from rupypy.ast import (Main, Block, Statement, Assignment,
    InstanceVariableAssignment, If, While, Class, Function, Argument, Return,
    Yield, BinOp, UnaryOp, Send, SendBlock, LookupConstant, Self, Variable,
    InstanceVariable, Array, Range, ConstantInt, ConstantFloat, ConstantSymbol,
    ConstantString)


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
        target = self.visit_arg(node.children[0])
        oper = node.children[1].additional_info
        value = self.visit_expr(node.children[2])
        return target.convert_to_assignment(oper, value)

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
        elif symname == "range":
            return self.visit_range(node)
        elif symname == "unary_op":
            return self.visit_unaryop(node)
        elif symname == "send":
            return self.visit_send(node)
        elif symname == "primary":
            return self.visit_primary(node)
        elif symname == "block":
            return self.visit_send_block(node)
        raise NotImplementedError(symname)

    def visit_subexpr(self, node):
        return BinOp(
            node.children[1].additional_info,
            self.visit_arg(node.children[0]),
            self.visit_arg(node.children[2]),
        )

    def visit_unaryop(self, node):
        return UnaryOp(
            node.children[0].additional_info,
            self.visit_arg(node.children[1]),
        )

    def visit_range(self, node):
        inclusive = node.children[1].additional_info == "..."
        return Range(
            self.visit_arg(node.children[0]),
            self.visit_arg(node.children[2]),
            inclusive=inclusive,
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
            if node.symbol in ["attribute", "subscript"]:
                if node.symbol == "attribute":
                    method = node.children[0].children[0].additional_info
                    if len(node.children) == 1:
                        args = []
                    else:
                        args = self.visit_send_args(node.children[1])
                elif node.symbol == "subscript":
                    args = [self.visit_arg(node.children[0])]
                    method = "[]"
                target = Send(
                    target,
                    method,
                    args,
                )
            elif node.symbol == "constant":
                target = LookupConstant(target, node.children[1].additional_info)
            else:
                raise NotImplementedError
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
        elif node.children[0].additional_info == "unless":
            return self.visit_unless(node)
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
        if symname == "NUMBER":
            return self.visit_number(node.children[0])
        elif symname == "symbol":
            return self.visit_symbol(node.children[0])
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
            Block([]),
        )

    def visit_unless(self, node):
        return If(
            self.visit_expr(node.children[1]),
            Block([]),
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
        superclass = None
        block_start_idx = 2
        if node.children[2].symbol == "LT":
            superclass = Variable(node.children[3].additional_info)
            block_start_idx += 2
        return Class(
            node.children[1].additional_info,
            superclass,
            self.visit_block(node, start_idx=block_start_idx, end_idx=len(node.children) - 1),
        )

    def visit_argdecl(self, node):
        if not node.children:
            return []
        return self.visit_arglist(node.children[0])

    def visit_arglist(self, node):
        # 0 indicates no defaults have been seen, 1 indicates a section of
        # defaults has been started (but not finished), and 2 indicates that
        # there have been defaults and then normal args after it, at this point
        # seeing another default argument is an error
        default_seen = 0
        args = []
        for n in node.children:
            name = n.children[0].additional_info
            if len(n.children) == 2:
                if default_seen == 2:
                    raise Exception
                default_seen = 1
                args.append(Argument(name, self.visit_arg(n.children[1])))
            else:
                if default_seen == 1:
                    default_seen = 2
                args.append(Argument(name))
        return args

    def visit_number(self, node):
        if "." in node.additional_info:
            return ConstantFloat(float(node.additional_info))
        else:
            return ConstantInt(int(node.additional_info))

    def visit_symbol(self, node):
        return ConstantSymbol(node.children[0].additional_info)

    def visit_string(self, node):
        end = len(node.additional_info) - 1
        assert end >= 0
        return ConstantString(node.additional_info[1:end])
