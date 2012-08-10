import os

from pypy.rlib.parsing.parsing import ParseError

from rupypy import ast
from rupypy.lexer import Lexer
from rupypy.utils.parsing import make_parse_function


with open(os.path.join(os.path.dirname(__file__), "grammar.txt")) as f:
    grammar = f.read()

_parse, ToASTVisitor = make_parse_function(grammar, Lexer)


class NewContextContextManager(object):
    def __init__(self, transformer):
        self.transformer = transformer

    def __enter__(self):
        self.transformer.stack.append(ExpressionContext())

    def __exit__(self, exc_type, exc_value, tb):
        self.transformer.stack.pop()


class SendContextManager(object):
    def __init__(self, transformer):
        self.transformer = transformer

    def __enter__(self):
        self.transformer.stack[-1].send_depth += 1

    def __exit__(self, exc_type, exc_value, tb):
        self.transformer.stack[-1].send_depth -= 1


class ExpressionContext(object):
    def __init__(self):
        self.send_depth = 0
        self.do_block = None


class Transformer(object):
    def __init__(self):
        self.stack = []

    def new_context(self):
        return NewContextContextManager(self)

    def send(self):
        return SendContextManager(self)

    def error(self, node):
        raise ParseError(node.getsourcepos(), None)

    def visit_main(self, node):
        return ast.Main(self.visit_block(node))

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
        return ast.Block(stmts)

    def visit_stmt(self, node):
        with self.new_context():
            if node.children[0].symbol == "return_expr":
                return ast.Return(self.visit_return(node.children[0]))
            elif node.children[0].symbol == "alias":
                return self.visit_alias(node.children[0])
            return ast.Statement(self.visit_expr(node.children[0]))

    def visit_return(self, node):
        if len(node.children) == 2:
            objs = self.visit_expr_splats(node.children[1])
            if len(objs) == 1:
                [obj] = objs
            else:
                obj = ast.Array(objs)
        else:
            obj = ast.Variable("nil", node.getsourcepos().lineno)
        return obj

    def visit_alias(self, node):
        return ast.Alias(
            ast.ConstantSymbol(node.children[1].additional_info),
            ast.ConstantSymbol(node.children[2].additional_info),
            node.getsourcepos().lineno
        )

    def visit_send_block(self, node):
        send = self.visit_real_send(node.children[0])

        block_args = []
        splat_arg = None
        start_idx = 2
        if node.children[2].symbol == "block_args":
            block_args, splat_arg = self.visit_block_args(node.children[2])
            start_idx += 1
        block = self.visit_block(node, start_idx=start_idx, end_idx=len(node.children) - 1)

        send_block = ast.SendBlock(block_args, splat_arg, block)

        if ((not isinstance(send, ast.Send) and self.stack[-1].send_depth == 1) or
            (isinstance(send, ast.Send) and send.block_arg is not None)):
            self.error(node)
        elif self.stack[-1].send_depth != 1:
            self.stack[-1].do_block = send_block
            return send
        elif isinstance(send, ast.Send):
            return ast.Send(
                send.receiver,
                send.method,
                send.args,
                send_block,
                node.getsourcepos().lineno
                )
        else:
            self.error(node)

    def visit_expr(self, node):
        if node.symbol == "inline_if":
            return ast.If(
                self.visit_expr(node.children[2]),
                ast.Block([self.visit_stmt(node.children[0])]),
                ast.Block([]),
            )
        elif node.symbol == "inline_unless":
            return ast.If(
                self.visit_expr(node.children[2]),
                ast.Block([]),
                ast.Block([self.visit_stmt(node.children[0])]),
            )
        elif node.symbol == "inline_until":
            return ast.Until(
                self.visit_expr(node.children[2]),
                ast.Block([self.visit_stmt(node.children[0])]),
            )
        elif node.symbol == "inline_while":
            return ast.While(
                self.visit_expr(node.children[2]),
                ast.Block([self.visit_stmt(node.children[0])]),
            )
        elif node.symbol == "inline_rescue":
            return ast.TryExcept(
                ast.Block([self.visit_stmt(node.children[0])]),
                [
                    ast.ExceptHandler(
                        [ast.LookupConstant(ast.Scope(node.getsourcepos().lineno), "StandardError", node.getsourcepos().lineno)],
                        None,
                        ast.Block([ast.Statement(self.visit_expr(node.children[2]))])
                    )
                ],
                ast.Block([]),
            )
        elif node.symbol == "contained_expr":
            if node.children[0].symbol == "assignment":
                return self.visit_assignment(node.children[0])
            elif node.children[0].symbol == "yield":
                return self.visit_yield(node.children[0])
            elif node.children[0].symbol == "literal_not":
                return ast.Not(self.visit_expr(node.children[0].children[1]))
            return self.visit_arg(node.children[0])
        elif node.symbol == "literal_bool":
            return self.visit_literal_bool(node)
        else:
            raise NotImplementedError(node.symbol)

    def visit_literal_bool(self, node):
        op = node.children[1].additional_info
        lhs = self.visit_expr(node.children[0])
        rhs = self.visit_expr(node.children[2])
        if op == "and":
            return ast.And(lhs, rhs)
        elif op == "or":
            return ast.Or(lhs, rhs)

    def visit_assignment(self, node):
        targets = [self.visit_arg(n) for n in node.children[0].children]
        oper = node.children[1].additional_info
        values = self.visit_expr_splats(node.children[2])
        if len(values) == 1:
            [value] = values
        else:
            value = ast.Array(values)
        if node.children[0].symbol == "assign_target_splat":
            if oper != "=":
                self.error(node.children[1])
            n_targets_pre_splat = 0
            for t in targets:
                if isinstance(t, ast.Splat):
                    break
                else:
                    n_targets_pre_splat += 1
            return ast.SplatAssignment(targets, value, n_targets_pre_splat)
        elif len(targets) == 1:
            [target] = targets
            target.validate_assignment(self, node)
            if oper == "=":
                return ast.Assignment(target, value)
            elif oper == "||=":
                return ast.OrEqual(target, value)
            elif oper == "&&=":
                return ast.AndEqual(target, value)
            else:
                return ast.AugmentedAssignment(oper[0], target, value)
        else:
            if oper != "=":
                self.error(node.children[1])
            return ast.MultiAssignment(targets, value)

    def visit_expr_splats(self, node):
        return [
            self.visit_splat(n) if n.symbol == "splat" else self.visit_expr(n)
            for n in node.children
        ]

    def visit_splat(self, node):
        return ast.Splat(self.visit_arg(node.children[0]))

    def visit_yield(self, node):
        args = []
        if len(node.children) == 2:
            args = self.visit_args(node.children[1])
        return ast.Yield(args, node.children[0].getsourcepos().lineno)

    def visit_arg(self, node):
        if node.symbol == "arg":
            node = node.children[0]

        symname = node.symbol
        if symname in ["comparison", "shiftive", "additive", "multitive", "bool", "match", "or", "and", "literal_bool", "pow"]:
            return self.visit_subexpr(node)
        elif symname == "range":
            return self.visit_range(node)
        elif symname == "unary_op":
            return self.visit_unaryop(node)
        elif symname == "splat":
            return self.visit_splat(node)
        elif symname == "ternary":
            return self.visit_ternary(node)
        elif symname == "send":
            return self.visit_send(node)
        elif symname == "primary":
            return self.visit_primary(node)
        elif symname == "do_block":
            with self.send():
                return self.visit_send_block(node)
        raise NotImplementedError(symname)

    def visit_subexpr(self, node):
        op = node.children[1].additional_info
        lhs = self.visit_arg(node.children[0])
        rhs = self.visit_arg(node.children[2])

        if op == "||":
            return ast.Or(lhs, rhs)
        elif op == "&&":
            return ast.And(lhs, rhs)
        elif op == "!~":
            return ast.Not(ast.BinOp("=~", lhs, rhs, node.getsourcepos().lineno))
        else:
            return ast.BinOp(op, lhs, rhs, node.getsourcepos().lineno)

    def visit_unaryop(self, node):
        op = node.children[0].additional_info
        value = self.visit_expr(node.children[1])
        if op == "!":
            return ast.Not(value)
        return ast.UnaryOp(op, value, node.getsourcepos().lineno)

    def visit_range(self, node):
        exclusive = node.children[1].additional_info == "..."
        return ast.Range(
            self.visit_arg(node.children[0]),
            self.visit_arg(node.children[2]),
            exclusive=exclusive,
        )

    def visit_ternary(self, node):
        return ast.If(
            self.visit_arg(node.children[0]),
            ast.Block([ast.Statement(self.visit_arg(node.children[2]))]),
            ast.Block([ast.Statement(self.visit_arg(node.children[4]))]),
        )

    def visit_send(self, node):
        if node.children[0].symbol == "real_send":
            with self.send():
                return self.visit_real_send(node.children[0])
        raise NotImplementedError

    def visit_real_send(self, node):
        if node.children[0].symbol == "ambigious_binop":
            node = node.children[0]
            lhs = self.visit_identifier(node.children[0])
            assert isinstance(lhs, ast.Variable)
            rhs = self.visit_arg(node.children[2])
            return ast.MaybeBinop(node.children[1].additional_info, lhs, rhs, node.getsourcepos().lineno)
        elif node.children[0].symbol in "global_send" or node.symbol == "global_paren_send":
            if node.symbol != "global_paren_send":
                node = node.children[0]
            if node.children[0].symbol == "global_paren_send":
                node = node.children[0]
            idx = 1
            args = []
            block_argument = None
            if idx < len(node.children) and node.children[idx].symbol == "send_args":
                args, block_argument = self.visit_send_args(node.children[idx])
                idx += 1
            if idx < len(node.children) and node.children[idx].symbol == "block":
                if block_argument:
                    self.error(node)
                block_args, splat_arg, block = self.visit_braces_block(node.children[idx])
                block_argument = ast.SendBlock(block_args, splat_arg, block)

            return ast.Send(
                ast.Self(node.getsourcepos().lineno),
                node.children[0].additional_info,
                args,
                block_argument,
                node.getsourcepos().lineno
            )

        if node.children[0].symbol == "global_paren_send":
            target = self.visit_real_send(node.children[0])
        else:
            target = self.visit_primary(node.children[0])

        n_trailers = len(node.children[1].children)
        for idx, trailer in enumerate(node.children[1].children):
            node = trailer.children[0]
            if node.symbol in ["attribute", "subscript"]:
                block_argument = None
                if node.symbol == "attribute":
                    method = node.children[0].additional_info
                    if len(node.children) == 1:
                        args = []
                    elif node.children[1].symbol == "block":
                        block_args, splat_arg, block = self.visit_braces_block(node.children[1])
                        target = ast.Send(
                            target,
                            method,
                            [],
                            ast.SendBlock(block_args, splat_arg, block),
                            node.getsourcepos().lineno
                        )
                        continue
                    else:
                        args, block_argument = self.visit_send_args(node.children[1])
                elif node.symbol == "subscript":
                    if len(node.children) > 1:
                        args = [self.visit_arg(n) for n in node.children[1].children]
                    else:
                        args = []
                    target = ast.Subscript(target, args, node.getsourcepos().lineno)
                    continue
                else:
                    assert False
                if len(node.children) == 3:
                    if block_argument is not None:
                        self.error(node)
                    block_args, splat_arg, block = self.visit_braces_block(node.children[2])
                    block_argument = ast.SendBlock(block_args, splat_arg, block)
                if idx == n_trailers - 1 and self.stack[-1].send_depth == 1 and self.stack[-1].do_block:
                    block_argument = self.stack[-1].do_block
                target = ast.Send(
                    target,
                    method,
                    args,
                    block_argument,
                    node.getsourcepos().lineno
                )
            elif node.symbol == "constant":
                target = ast.LookupConstant(target, node.children[1].additional_info, node.getsourcepos().lineno)
            else:
                raise NotImplementedError
        return target

    def visit_send_args(self, node):
        block_argument = None
        args = []
        idx = 0
        if node.children[idx].symbol == "args":
            args = self.visit_args(node.children[idx])
            idx += 1
        if idx < len(node.children) and node.children[idx].symbol == "block_arg":
            block_argument = ast.BlockArgument(self.visit_arg(node.children[idx].children[0]))
        return args, block_argument

    def visit_args(self, node):
        args = []
        assocs = []
        for n in node.children:
            if n.symbol == "assoc":
                assocs.append(self.visit_assoc(n))
            elif assocs:
                self.error(node)
            else:
                args.append(self.visit_arg(n))
        if assocs:
            args.append(ast.Hash(assocs))
        return args

    def visit_braces_block(self, node):
        block_args = []
        splat_arg = None
        start_idx = 0
        if start_idx < len(node.children) and node.children[start_idx].symbol == "block_args":
            block_args, splat_arg = self.visit_block_args(node.children[start_idx])
            start_idx += 1
        block = self.visit_block(node, start_idx=start_idx)
        return block_args, splat_arg, block

    def visit_primary(self, node):
        if node.children[0].symbol == "literal":
            return self.visit_literal(node.children[0])
        elif node.children[0].symbol == "varname":
            return self.visit_varname(node.children[0])
        elif node.children[0].additional_info == "(":
            return self.visit_expr(node.children[1])
        elif node.children[0].additional_info == "[":
            return self.visit_array(node)
        elif node.children[0].additional_info == "{":
            return self.visit_hash(node)
        elif node.children[0].additional_info == "if":
            return self.visit_if(node)
        elif node.children[0].additional_info == "unless":
            return self.visit_unless(node)
        elif node.children[0].additional_info == "while":
            return self.visit_while(node)
        elif node.children[0].additional_info == "until":
            return self.visit_until(node)
        elif node.children[0].additional_info == "def":
            return self.visit_def(node)
        elif node.children[0].additional_info == "class":
            return self.visit_class(node)
        elif node.children[0].additional_info == "module":
            return self.visit_module(node)
        elif node.children[0].additional_info == "begin":
            return self.visit_begin(node)
        elif node.children[0].additional_info == "case":
            return self.visit_case(node)
        elif node.children[0].symbol == "UNBOUND_COLONCOLON":
            return ast.LookupConstant(None, node.children[1].additional_info, node.getsourcepos().lineno)
        raise NotImplementedError(node.symbol)

    def visit_array(self, node):
        contents = node.children[1]
        if contents.children:
            items = self.visit_args(contents.children[0])
        else:
            items = []
        return ast.Array(items)

    def visit_hash(self, node):
        contents = node.children[1]
        if contents.children:
            items = [
                self.visit_assoc(n)
                for n in contents.children[0].children
            ]
        else:
            items = []
        return ast.Hash(items)

    def visit_assoc(self, node):
        return self.visit_expr(node.children[0]), self.visit_expr(node.children[2])

    def visit_literal(self, node):
        symname = node.children[0].symbol
        if symname == "NUMBER":
            return self.visit_number(node.children[0])
        elif symname == "symbol":
            return self.visit_symbol(node.children[0])
        elif symname == "strings" or symname == "real_strings":
            return self.visit_strings(node.children[0])
        elif symname == "regexp":
            return self.visit_regexp(node.children[0])
        elif symname == "shellout":
            return self.visit_shellout(node.children[0])
        elif symname == "qwords":
            return self.visit_qwords(node.children[0])
        elif symname == "quote":
            return self.visit_quote(node.children[0])
        raise NotImplementedError(symname)

    def visit_varname(self, node):
        node = node.children[0]
        if node.symbol == "INSTANCE_VAR":
            return ast.InstanceVariable(node.additional_info)
        elif node.symbol == "CLASS_VAR":
            return ast.ClassVariable(node.additional_info)
        elif node.symbol == "GLOBAL":
            return ast.Global(node.additional_info)
        elif node.symbol == "IDENTIFIER":
            return self.visit_identifier(node)
        elif node.symbol == "CONSTANT":
            return ast.LookupConstant(ast.Scope(node.getsourcepos().lineno), node.additional_info, node.getsourcepos().lineno)

    def visit_identifier(self, node):
        name = node.additional_info
        lineno = node.getsourcepos().lineno
        if name == "self":
            return ast.Self(lineno)
        else:
            return ast.Variable(name, lineno)

    def visit_if(self, node):
        if_node = node.children[1]
        if_cond = self.visit_expr(if_node.children[0])
        if_block = self.visit_block(if_node, start_idx=2)

        idx = 2
        conditions = []
        if len(node.children) > idx and node.children[idx].symbol == "elsifs":
            for n in node.children[idx].children:
                cond = self.visit_expr(n.children[1])
                body = self.visit_block(n, start_idx=3)
                conditions.append((cond, body))
            idx += 1
        if len(node.children) > idx and node.children[idx].symbol == "else":
            else_node = node.children[idx]
            else_block = self.visit_block(else_node, start_idx=1)
        else:
            else_block = ast.Block([])

        for idx in range(len(conditions) - 1, -1, -1):
            cond, block = conditions[idx]
            else_block = ast.Block([
                ast.Statement(ast.If(cond, block, else_block))
            ])

        return ast.If(if_cond, if_block, else_block)

    def visit_unless(self, node):
        unless_node = node.children[1]
        unless_cond = self.visit_expr(unless_node.children[0])
        unless_block = self.visit_block(unless_node, start_idx=2)

        idx = 2
        if len(node.children) > idx and node.children[idx].symbol == "else":
            else_node = node.children[2]
            else_block = self.visit_block(else_node, start_idx=1)
        else:
            else_block = ast.Block([])
        return ast.If(
            unless_cond,
            else_block,
            unless_block,
        )

    def visit_while(self, node):
        return ast.While(
            self.visit_expr(node.children[1]),
            self.visit_block(node, start_idx=3, end_idx=len(node.children) - 1),
        )

    def visit_until(self, node):
        return ast.Until(
            self.visit_expr(node.children[1]),
            self.visit_block(node, start_idx=3, end_idx=len(node.children) - 1),
        )

    def visit_def(self, node):
        name_node = node.children[1]
        if len(name_node.children) == 1:
            parent = None
            name = name_node.children[0].additional_info
        else:
            parent = self.visit_varname(name_node.children[0])
            name = name_node.children[1].additional_info
        args, splat_arg, block_arg = self.visit_argdecl(node.children[2])

        idx = 3
        while idx < len(node.children) and node.children[idx].symbol not in ["rescue", "ensure"]:
            idx += 1
        body = self.visit_block(node, start_idx=3, end_idx=idx)
        handlers = []
        while idx < len(node.children) and node.children[idx].symbol == "rescue":
            handlers.append(self.visit_rescue(node.children[idx]))
            idx += 1
        if handlers:
            body = ast.TryExcept(body, handlers, ast.Block([]))
        if idx < len(node.children) and  node.children[idx].symbol == "ensure":
            ensure_node = node.children[idx]
            block = self.visit_block(ensure_node, start_idx=1)
            body = ast.TryFinally(body, block)

        return ast.Function(
            parent,
            name,
            args,
            splat_arg,
            block_arg,
            body,
        )

    def visit_class(self, node):
        if node.children[1].symbol == "LSHIFT":
            return ast.SingletonClass(
                self.visit_arg(node.children[2]),
                self.visit_block(node, start_idx=3, end_idx=len(node.children) - 1),
                node.getsourcepos().lineno,
            )

        superclass = None
        block_start_idx = 2
        if node.children[2].symbol == "LT":
            superclass = self.visit_arg(node.children[3])
            block_start_idx += 2
        return ast.Class(
            node.children[1].additional_info,
            superclass,
            self.visit_block(node, start_idx=block_start_idx, end_idx=len(node.children) - 1),
        )

    def visit_module(self, node):
        return ast.Module(
            node.children[1].additional_info,
            self.visit_block(node, start_idx=2, end_idx=len(node.children) - 1)
        )

    def visit_begin(self, node):
        idx = 0
        while idx < len(node.children):
            if node.children[idx].symbol in ["rescue", "ensure", "else"]:
                break
            idx += 1
        body_block = self.visit_block(node, start_idx=1, end_idx=idx)
        handlers = []
        while idx < len(node.children) and node.children[idx].symbol == "rescue":
            handlers.append(self.visit_rescue(node.children[idx]))
            idx += 1

        if idx < len(node.children) and node.children[idx].symbol == "else":
            else_node = node.children[idx]
            else_block = self.visit_block(else_node, start_idx=1)
            has_else_block = True
        else:
            else_block = ast.Block([])
            has_else_block = False

        if handlers or has_else_block:
            body_block = ast.TryExcept(body_block, handlers, else_block)

        if idx < len(node.children) and node.children[idx].symbol == "ensure":
            ensure_node = node.children[idx]
            block = self.visit_block(ensure_node, start_idx=1)
            body_block = ast.TryFinally(body_block, block)
        return body_block

    def visit_rescue(self, node):
        exceptions = []
        idx = 1
        if node.children[1].symbol == "exprs":
            exceptions = [self.visit_expr(n) for n in node.children[1].children]
            idx += 1
        target = None
        if node.children[idx].symbol == "ARROW":
            target = self.visit_varname(node.children[idx + 1])
            idx += 2
        block = self.visit_block(node, start_idx=idx)
        return ast.ExceptHandler(exceptions, target, block)

    def visit_case(self, node):
        if node.children[1].symbol == "whens":
            return self.visit_case_without_expr(node)
        cond = self.visit_expr(node.children[1])
        whens = []
        for n in node.children[2].children:
            exprs = [self.visit_expr(w) for w in n.children[1].children]
            block = self.visit_block(n, start_idx=3)
            whens.append((exprs, block))
        if node.children[3].symbol == "else":
            elsebody = self.visit_block(node.children[3], start_idx=1)
        else:
            elsebody = ast.Block([])
        return ast.Case(
            cond,
            whens,
            elsebody,
        )

    def visit_case_without_expr(self, node):
        whens = node.children[1].children
        conditions = []
        for when in whens:
            exprs = when.children[1]
            cond = self.visit_expr(exprs.children[0])
            for expr in exprs.children[1:]:
                cond = ast.Or(cond, self.visit_expr(expr))
            if len(when.children) == 4:
                body = self.visit_block(when.children[3])
            else:
                body = ast.Block([])
            conditions.append((cond, body))

        if node.children[2].symbol == "else":
            else_block = self.visit_block(node.children[2], start_idx=1)
        else:
            else_block = ast.Block([])

        for idx in range(len(conditions) - 1, 0, -1):
            cond, block = conditions[idx]
            else_block = ast.Block([
                ast.Statement(ast.If(cond, block, else_block))
            ])
        return ast.If(conditions[0][0], conditions[0][1], else_block)

    def visit_argdecl(self, node):
        if not node.children:
            return [], None, None
        return self.visit_arglist(node.children[0])

    def visit_block_args(self, node):
        block_args = []
        splat_arg = None
        if node.children:
            block_args, splat_arg, _ = self.visit_arglist(node.children[0])
        return block_args, splat_arg

    def visit_arglist(self, node):
        # 0 indicates no defaults have been seen, 1 indicates a section of
        # defaults has been started (but not finished), and 2 indicates that
        # there have been defaults and then normal args after it, at this point
        # seeing another default argument is an error
        default_seen = 0
        block_arg = None
        splat_arg = None
        args = []
        for n in node.children:
            if block_arg:
                self.error(n)
            if len(n.children) == 2 and n.children[0].symbol == "AMP":
                block_arg = n.children[1].additional_info
            else:
                if splat_arg:
                    self.error(n)
                if len(n.children) == 1 and n.children[0].symbol == "UNARY_STAR":
                    splat_arg = ""
                elif len(n.children) == 2 and n.children[0].symbol == "UNARY_STAR":
                    splat_arg = n.children[1].additional_info
                elif len(n.children) == 2:
                    name = n.children[0].additional_info
                    if default_seen == 2:
                        self.error(n)
                    default_seen = 1
                    args.append(ast.Argument(name, self.visit_arg(n.children[1])))
                else:
                    name = n.children[0].additional_info
                    if default_seen == 1:
                        default_seen = 2
                    args.append(ast.Argument(name))
        return args, splat_arg, block_arg

    def visit_number(self, node):
        if "." in node.additional_info or "E" in node.additional_info:
            return ast.ConstantFloat(float(node.additional_info))
        elif "X" in node.additional_info:
            return ast.ConstantInt(int(node.additional_info[2:], 16))
        elif "O" in node.additional_info:
            return ast.ConstantInt(int(node.additional_info[2:], 8))
        elif "B" in node.additional_info:
            return ast.ConstantInt(int(node.additional_info[2:], 2))
        else:
            return ast.ConstantInt(int(node.additional_info))

    def visit_symbol(self, node):
        node = node.children[0]
        if node.symbol == "varname":
            return ast.ConstantSymbol(node.children[0].additional_info)
        elif node.symbol == "SSTRING":
            return ast.ConstantSymbol(node.additional_info)
        else:
            return ast.Symbol(self.visit_dstring(node), node.getsourcepos().lineno)

    def visit_strings(self, node):
        if len(node.children) == 1:
            if node.children[0].symbol == "SSTRING":
                return self.visit_sstring(node.children[0])
            elif node.children[0].symbol == "string":
                return self.visit_dstring(node.children[0])
            else:
                self.error(node.children[0])
        else:
            components = []
            for n in node.children:
                if n.symbol == "SSTRING":
                    components.append(self.visit_sstring(n))
                elif n.symbol == "string":
                    components.append(self.visit_dstring(n))
                elif n.symbol == "quote":
                    components.append(self.visit_quote(n))
            return ast.DynamicString(components)

    def visit_sstring(self, node):
        return ast.ConstantString(node.additional_info)

    def visit_dstring(self, node):
        components = []
        for n in node.children:
            if n.symbol == "STRING_VALUE":
                components.append(ast.ConstantString(n.additional_info))
            else:
                stmt = self.visit_stmt(n)
                assert isinstance(stmt, ast.Statement)
                components.append(stmt.expr)
        if components:
            return ast.DynamicString(components)
        else:
            return ast.ConstantString("")

    def visit_quote(self, node):
        return self.visit_dstring(node.children[0])

    def visit_regexp(self, node):
        if len(node.children[0].children) == 0:
            return ast.ConstantRegexp("")
        elif node.children[0].children[0].symbol == "STRING_VALUE":
            return ast.ConstantRegexp(node.children[0].children[0].additional_info)
        else:
            return ast.DynamicRegexp(self.visit_dstring(node.children[0]))

    def visit_shellout(self, node):
        return ast.Send(
            ast.Self(node.getsourcepos().lineno),
            "`",
            [self.visit_dstring(node.children[0])],
            None,
            node.getsourcepos().lineno
        )

    def visit_qwords(self, node):
        contents = node.children[0]
        if contents.children:
            items = [self.visit_dstring(n) for n in contents.children]
        else:
            items = []
        return ast.Array(items)
