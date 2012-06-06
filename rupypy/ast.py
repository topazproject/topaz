from __future__ import absolute_import

from pypy.rlib.objectmodel import we_are_translated

from rupypy import consts
from rupypy.astcompiler import CompilerContext, SymbolTable, BlockSymbolTable


class Node(object):
    _attrs_ = ["lineno"]

    def __init__(self, lineno):
        self.lineno = lineno

    def __eq__(self, other):
        if not isinstance(other, Node):
            return NotImplemented
        return type(self) is type(other) and self.__dict__ == other.__dict__

    def locate_symbols(self, symtable):
        if we_are_translated():
            raise NotImplementedError
        else:
            raise NotImplementedError(type(self).__name__)

    def compile(self, ctx):
        if we_are_translated():
            raise NotImplementedError
        else:
            raise NotImplementedError(type(self).__name__)


class Main(Node):
    def __init__(self, block):
        self.block = block

    def locate_symbols(self, symtable):
        self.block.locate_symbols(symtable)

    def compile(self, ctx):
        self.block.compile(ctx)
        ctx.emit(consts.DISCARD_TOP)
        ctx.emit(consts.LOAD_CONST, ctx.create_const(ctx.space.w_true))
        ctx.emit(consts.RETURN)


class Block(Node):
    def __init__(self, stmts):
        if not stmts:
            stmts = [Statement(Variable("nil", -1))]
        # The last item shouldn't be popped.
        stmts[-1].dont_pop = True

        self.stmts = stmts

    def locate_symbols(self, symtable):
        for stmt in self.stmts:
            stmt.locate_symbols(symtable)

    def compile(self, ctx):
        for idx, stmt in enumerate(self.stmts):
            stmt.compile(ctx)


class BaseStatement(Node):
    pass


class Statement(BaseStatement):
    def __init__(self, expr):
        self.expr = expr
        self.dont_pop = False

    def locate_symbols(self, symtable):
        self.expr.locate_symbols(symtable)

    def compile(self, ctx):
        self.expr.compile(ctx)
        if not self.dont_pop:
            ctx.emit(consts.DISCARD_TOP)


class If(Node):
    def __init__(self, cond, body, elsebody):
        self.cond = cond
        self.body = body
        self.elsebody = elsebody

    def locate_symbols(self, symtable):
        self.cond.locate_symbols(symtable)
        self.body.locate_symbols(symtable)
        self.elsebody.locate_symbols(symtable)

    def compile(self, ctx):
        end = ctx.new_block()
        otherwise = ctx.new_block()
        self.cond.compile(ctx)
        ctx.emit_jump(consts.JUMP_IF_FALSE, otherwise)
        self.body.compile(ctx)
        ctx.emit_jump(consts.JUMP, end)
        ctx.use_next_block(otherwise)
        self.elsebody.compile(ctx)
        ctx.use_next_block(end)


class While(Node):
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

    def locate_symbols(self, symtable):
        self.cond.locate_symbols(symtable)
        self.body.locate_symbols(symtable)

    def compile(self, ctx):
        end = ctx.new_block()
        loop = ctx.new_block()

        ctx.use_next_block(loop)
        self.cond.compile(ctx)
        ctx.emit_jump(consts.JUMP_IF_FALSE, end)
        self.body.compile(ctx)
        # The body leaves an extra item on the stack, discard it.
        ctx.emit(consts.DISCARD_TOP)
        ctx.emit_jump(consts.JUMP, loop)
        ctx.use_next_block(end)
        # For now, while always returns a nil, eventually it can also return a
        # value from a break
        ctx.emit(consts.LOAD_CONST, ctx.create_const(ctx.space.w_nil))


class Until(Node):
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

    def locate_symbols(self, symtable):
        self.cond.locate_symbols(symtable)
        self.body.locate_symbols(symtable)

    def compile(self, ctx):
        end = ctx.new_block()
        loop = ctx.new_block()

        ctx.use_next_block(loop)
        self.cond.compile(ctx)
        ctx.emit_jump(consts.JUMP_IF_TRUE, end)
        self.body.compile(ctx)
        ctx.emit(consts.DISCARD_TOP)
        ctx.emit_jump(consts.JUMP, loop)
        ctx.use_next_block(end)
        ctx.emit(consts.LOAD_CONST, ctx.create_const(ctx.space.w_nil))


class TryExcept(Node):
    def __init__(self, body, except_handlers):
        self.body = body
        self.except_handlers = except_handlers

    def locate_symbols(self, symtable):
        self.body.locate_symbols(symtable)
        for handler in self.except_handlers:
            handler.locate_symbols(symtable)

    def compile(self, ctx):
        exc = ctx.new_block()
        end = ctx.new_block()
        ctx.emit_jump(consts.SETUP_EXCEPT, exc)
        ctx.use_next_block(ctx.new_block())
        self.body.compile(ctx)
        ctx.emit(consts.POP_BLOCK)
        ctx.emit_jump(consts.JUMP, end)
        ctx.use_next_block(exc)
        for handler in self.except_handlers:
            next_except = ctx.new_block()
            if handler.exception is not None:
                handler.exception.compile(ctx)
                ctx.emit(consts.COMPARE_EXC)
                ctx.emit_jump(consts.JUMP_IF_FALSE, next_except)
            if handler.name:
                ctx.emit(consts.STORE_LOCAL, ctx.symtable.get_local_num(handler.name))
            ctx.emit(consts.DISCARD_TOP)
            ctx.emit(consts.DISCARD_TOP)
            handler.body.compile(ctx)
            ctx.emit_jump(consts.JUMP, end)
            ctx.use_next_block(next_except)
        ctx.emit(consts.END_FINALLY)
        ctx.use_next_block(end)


class ExceptHandler(Node):
    def __init__(self, exception, name, body):
        self.exception = exception
        self.name = name
        self.body = body

    def locate_symbols(self, symtable):
        if self.exception is not None:
            self.exception.locate_symbols(symtable)
        if self.name is not None:
            symtable.declare_local(self.name)
        self.body.locate_symbols(symtable)


class TryFinally(Node):
    def __init__(self, body, finally_body):
        self.body = body
        self.finally_body = finally_body

    def locate_symbols(self, symtable):
        self.body.locate_symbols(symtable)
        self.finally_body.locate_symbols(symtable)

    def compile(self, ctx):
        end = ctx.new_block()
        ctx.emit_jump(consts.SETUP_FINALLY, end)
        ctx.use_next_block(ctx.new_block())
        self.body.compile(ctx)
        ctx.emit(consts.POP_BLOCK)
        # Put a None on the stack where an exception would be.
        ctx.emit(consts.LOAD_CONST, ctx.create_const(ctx.space.w_nil))
        ctx.use_next_block(end)
        self.finally_body.compile(ctx)
        ctx.emit(consts.DISCARD_TOP)
        ctx.emit(consts.END_FINALLY)


class Class(Node):
    def __init__(self, name, superclass, body):
        self.name = name
        self.superclass = superclass
        self.body = body

    def locate_symbols(self, symtable):
        body_symtable = SymbolTable()
        symtable.add_subscope(self, body_symtable)
        self.body.locate_symbols(body_symtable)

    def compile(self, ctx):
        ctx.emit(consts.LOAD_SCOPE)
        ctx.emit(consts.LOAD_CONST, ctx.create_symbol_const(self.name))
        if self.superclass is None:
            ctx.emit(consts.LOAD_CONST, ctx.create_const(ctx.space.w_nil))
        else:
            self.superclass.compile(ctx)
        ctx.emit(consts.BUILD_CLASS)

        body_ctx = ctx.get_subctx(self.name, self)
        self.body.compile(body_ctx)
        body_ctx.emit(consts.DISCARD_TOP)
        body_ctx.emit(consts.LOAD_CONST, body_ctx.create_const(body_ctx.space.w_nil))
        body_ctx.emit(consts.RETURN)
        bytecode = body_ctx.create_bytecode([], [], None, None)

        ctx.emit(consts.LOAD_CONST, ctx.create_const(bytecode))
        ctx.emit(consts.EVALUATE_CLASS)


class SingletonClass(Node):
    def __init__(self, value, body, lineno):
        Node.__init__(self, lineno)
        self.value = value
        self.body = body

    def locate_symbols(self, symtable):
        self.value.locate_symbols(symtable)

        body_symtable = SymbolTable()
        symtable.add_subscope(self, body_symtable)
        self.body.locate_symbols(body_symtable)

    def compile(self, ctx):
        Send(self.value, "singleton_class", [], None, self.lineno).compile(ctx)

        body_ctx = ctx.get_subctx("singletonclass", self)
        self.body.compile(body_ctx)
        body_ctx.emit(consts.DISCARD_TOP)
        body_ctx.emit(consts.LOAD_CONST, body_ctx.create_const(body_ctx.space.w_nil))
        body_ctx.emit(consts.RETURN)
        bytecode = body_ctx.create_bytecode([], [], None, None)

        ctx.emit(consts.LOAD_CONST, ctx.create_const(bytecode))
        ctx.emit(consts.EVALUATE_CLASS)


class Module(Node):
    def __init__(self, name, body):
        self.name = name
        self.body = body

    def locate_symbols(self, symtable):
        body_symtable = SymbolTable()
        symtable.add_subscope(self, body_symtable)
        self.body.locate_symbols(body_symtable)

    def compile(self, ctx):
        body_ctx = ctx.get_subctx(self.name, self)
        self.body.compile(body_ctx)
        body_ctx.emit(consts.DISCARD_TOP)
        body_ctx.emit(consts.LOAD_CONST, body_ctx.create_const(body_ctx.space.w_nil))
        body_ctx.emit(consts.RETURN)
        bytecode = body_ctx.create_bytecode([], [], None, None)

        ctx.emit(consts.LOAD_SCOPE)
        ctx.emit(consts.LOAD_CONST, ctx.create_symbol_const(self.name))
        ctx.emit(consts.LOAD_CONST, ctx.create_const(bytecode))
        ctx.emit(consts.BUILD_MODULE)


class Function(Node):
    def __init__(self, parent, name, args, splat_arg, block_arg, body):
        self.parent = parent
        self.name = name
        self.args = args
        self.splat_arg = splat_arg
        self.block_arg = block_arg
        self.body = body

    def locate_symbols(self, symtable):
        if self.parent is not None:
            self.parent.locate_symbols(symtable)

        body_symtable = SymbolTable()
        symtable.add_subscope(self, body_symtable)
        for arg in self.args:
            body_symtable.declare_local(arg.name)
            if arg.defl is not None:
                arg.defl.locate_symbols(body_symtable)
        if self.block_arg is not None:
            body_symtable.declare_local(self.block_arg)
        if self.splat_arg is not None:
            body_symtable.declare_local(self.splat_arg)
        self.body.locate_symbols(body_symtable)

    def compile(self, ctx):
        function_ctx = ctx.get_subctx(self.name, self)
        defaults = []
        for arg in self.args:
            if function_ctx.symtable.is_local(arg.name):
                function_ctx.symtable.get_local_num(arg.name)
            elif function_ctx.symtable.is_cell(arg.name):
                function_ctx.symtable.get_cell_num(arg.name)

            arg_ctx = CompilerContext(ctx.space, self.name, function_ctx.symtable, ctx.filepath)
            if arg.defl is not None:
                arg.defl.compile(arg_ctx)
                arg_ctx.emit(consts.RETURN)
                bc = arg_ctx.create_bytecode([], [], None, None)
                defaults.append(bc)
        if self.block_arg is not None:
            if function_ctx.symtable.is_local(self.block_arg):
                function_ctx.symtable.get_local_num(self.block_arg)
            elif function_ctx.symtable.is_cell(self.block_arg):
                function_ctx.symtable.get_cell_num(self.block_arg)

        self.body.compile(function_ctx)
        function_ctx.emit(consts.RETURN)
        arg_names = [a.name for a in self.args]
        bytecode = function_ctx.create_bytecode(
            arg_names, defaults, self.splat_arg, self.block_arg
        )

        if self.parent is None:
            ctx.emit(consts.LOAD_SCOPE)
        else:
            self.parent.compile(ctx)
        ctx.emit(consts.LOAD_CONST, ctx.create_symbol_const(self.name))
        ctx.emit(consts.LOAD_CONST, ctx.create_symbol_const(self.name))
        ctx.emit(consts.LOAD_CONST, ctx.create_const(bytecode))
        ctx.emit(consts.BUILD_FUNCTION)
        if self.parent is None:
            ctx.emit(consts.DEFINE_FUNCTION)
        else:
            ctx.emit(consts.ATTACH_FUNCTION)


class Argument(Node):
    def __init__(self, name, defl=None):
        self.name = name
        self.defl = defl


class Case(Node):
    def __init__(self, cond, whens, elsebody):
        self.cond = cond
        self.whens = whens
        self.elsebody = elsebody

    def locate_symbols(self, symtable):
        self.cond.locate_symbols(symtable)
        for when, block in self.whens:
            for expr in when:
                expr.locate_symbols(symtable)
            block.locate_symbols(symtable)
        self.elsebody.locate_symbols(symtable)

    def compile(self, ctx):
        end = ctx.new_block()

        self.cond.compile(ctx)
        for when, block in self.whens:
            next_when = ctx.new_block()
            when_block = ctx.new_block()

            for expr in when:
                next_expr = ctx.new_block()
                ctx.emit(consts.DUP_TOP)
                expr.compile(ctx)
                ctx.emit(consts.SEND, ctx.create_symbol_const("==="), 1)
                ctx.emit_jump(consts.JUMP_IF_TRUE, when_block)
                ctx.use_next_block(next_expr)
            ctx.emit_jump(consts.JUMP, next_when)
            ctx.use_next_block(when_block)
            ctx.emit(consts.DISCARD_TOP)
            block.compile(ctx)
            ctx.emit_jump(consts.JUMP, end)
            ctx.use_next_block(next_when)
        ctx.emit(consts.DISCARD_TOP)
        self.elsebody.compile(ctx)
        ctx.use_next_block(end)


class Return(BaseStatement):
    def __init__(self, expr):
        self.expr = expr

    def locate_symbols(self, symtable):
        self.expr.locate_symbols(symtable)

    def compile(self, ctx):
        self.expr.compile(ctx)
        if isinstance(ctx.symtable, BlockSymbolTable):
            ctx.emit(consts.RAISE_RETURN)
        else:
            ctx.emit(consts.RETURN)


class Yield(Node):
    def __init__(self, args, lineno):
        Node.__init__(self, lineno)
        self.args = args

    def locate_symbols(self, symtable):
        for arg in self.args:
            arg.locate_symbols(symtable)

    def compile(self, ctx):
        for arg in self.args:
            arg.compile(ctx)
        ctx.current_lineno = self.lineno
        ctx.emit(consts.YIELD, len(self.args))


class Assignment(Node):
    def __init__(self, target, value):
        self.target = target
        self.value = value

    def locate_symbols(self, symtable):
        self.target.locate_symbols_assignment(symtable)
        self.value.locate_symbols(symtable)

    def compile(self, ctx):
        self.target.compile_receiver(ctx)
        self.value.compile(ctx)
        self.target.compile_store(ctx)


class AugmentedAssignment(Node):
    def __init__(self, oper, target, value):
        self.oper = oper
        self.target = target
        self.value = value

    def locate_symbols(self, symtable):
        self.target.locate_symbols_assignment(symtable)
        self.value.locate_symbols(symtable)

    def compile(self, ctx):
        dup_needed = self.target.compile_receiver(ctx)
        if dup_needed == 1:
            ctx.emit(consts.DUP_TOP)
        elif dup_needed == 2:
            ctx.emit(consts.DUP_TWO)
        self.target.compile_load(ctx)
        self.value.compile(ctx)
        ctx.emit(consts.SEND, ctx.create_symbol_const(self.oper), 1)
        self.target.compile_store(ctx)


class OrEqual(Node):
    def __init__(self, target, value):
        self.target = target
        self.value = value

    def locate_symbols(self, symtable):
        self.target.locate_symbols_assignment(symtable)
        self.value.locate_symbols(symtable)

    def compile(self, ctx):
        otherwise = ctx.new_block()
        end = ctx.new_block()

        dup_needed = self.target.compile_receiver(ctx)
        if dup_needed == 1:
            ctx.emit(consts.DUP_TOP)
        elif dup_needed == 2:
            ctx.emit(consts.DUP_TWO)
        self.target.compile_load(ctx)
        ctx.emit(consts.DUP_TOP)
        ctx.emit_jump(consts.JUMP_IF_TRUE, end)
        ctx.use_next_block(otherwise)
        ctx.emit(consts.DISCARD_TOP)
        self.value.compile(ctx)
        ctx.use_next_block(end)
        self.target.compile_store(ctx)


class MultiAssignment(Node):
    def __init__(self, targets, value):
        self.targets = targets
        self.value = value

    def locate_symbols(self, symtable):
        for target in self.targets:
            target.locate_symbols_assignment(symtable)
        self.value.locate_symbols(symtable)

    def compile(self, ctx):
        self.value.compile(ctx)
        ctx.emit(consts.DUP_TOP)
        ctx.emit(consts.COERCE_ARRAY)
        ctx.emit(consts.UNPACK_SEQUENCE, len(self.targets))
        for target in self.targets:
            elems = target.compile_receiver(ctx)
            if elems == 1:
                ctx.emit(consts.ROT_TWO)
            elif elems == 2:
                ctx.emit(consts.ROT_THREE)
                ctx.emit(consts.ROT_THREE)
            target.compile_store(ctx)
            ctx.emit(consts.DISCARD_TOP)


class BinOp(Node):
    def __init__(self, op, left, right, lineno):
        Node.__init__(self, lineno)
        self.op = op
        self.left = left
        self.right = right

    def locate_symbols(self, symtable):
        self.left.locate_symbols(symtable)
        self.right.locate_symbols(symtable)

    def compile(self, ctx):
        Send(self.left, self.op, [self.right], None, self.lineno).compile(ctx)


class MaybeBinop(Node):
    def __init__(self, op, left, right, lineno):
        Node.__init__(self, lineno)
        self.op = op
        self.left = left
        self.right = right

    def locate_symbols(self, symtable):
        if symtable.is_defined(self.left.name):
            self.left.locate_symbols(symtable)
        self.right.locate_symbols(symtable)

    def compile(self, ctx):
        if ctx.symtable.is_defined(self.left.name):
            Send(self.left, self.op, [self.right], None, self.lineno).compile(ctx)
        else:
            Send(
                Self(self.lineno),
                self.left.name,
                [UnaryOp(self.op, self.right, self.lineno)],
                None,
                self.lineno
            ).compile(ctx)


class UnaryOp(Node):
    def __init__(self, op, value, lineno):
        Node.__init__(self, lineno)
        self.op = op
        self.value = value

    def locate_symbols(self, symtable):
        self.value.locate_symbols(symtable)

    def compile(self, ctx):
        Send(self.value, self.op + "@", [], None, self.lineno).compile(ctx)


class Or(Node):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def locate_symbols(self, symtable):
        self.lhs.locate_symbols(symtable)
        self.rhs.locate_symbols(symtable)

    def compile(self, ctx):
        end = ctx.new_block()
        otherwise = ctx.new_block()

        self.lhs.compile(ctx)
        ctx.emit(consts.DUP_TOP)
        ctx.emit_jump(consts.JUMP_IF_TRUE, end)
        ctx.use_next_block(otherwise)
        ctx.emit(consts.DISCARD_TOP)
        self.rhs.compile(ctx)
        ctx.use_next_block(end)


class And(Node):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def locate_symbols(self, symtable):
        self.lhs.locate_symbols(symtable)
        self.rhs.locate_symbols(symtable)

    def compile(self, ctx):
        end = ctx.new_block()
        otherwise = ctx.new_block()

        self.lhs.compile(ctx)
        ctx.emit(consts.DUP_TOP)
        ctx.emit_jump(consts.JUMP_IF_FALSE, end)
        ctx.use_next_block(otherwise)
        ctx.emit(consts.DISCARD_TOP)
        self.rhs.compile(ctx)
        ctx.use_next_block(end)

class Not(Node):
    def __init__(self, value):
        self.value = value

    def locate_symbols(self, symtable):
        self.value.locate_symbols(symtable)

    def compile(self, ctx):
        self.value.compile(ctx)
        ctx.emit(consts.UNARY_NOT)

class Send(Node):
    def __init__(self, receiver, method, args, block_arg, lineno):
        self.receiver = receiver
        self.method = method
        self.args = args
        self.block_arg = block_arg
        self.lineno = lineno

    def validate_assignment(self, transformer, node):
        if self.args or self.block_arg:
            transformer.error(node)

    def locate_symbols(self, symtable):
        self.receiver.locate_symbols(symtable)
        for arg in self.args:
            arg.locate_symbols(symtable)

        if self.block_arg is not None:
            self.block_arg.locate_symbols(symtable)

    def locate_symbols_assignment(self, symtable):
        self.receiver.locate_symbols(symtable)

    def compile(self, ctx):
        self.receiver.compile(ctx)
        if self.is_splat():
            for arg in self.args:
                arg.compile(ctx)
                if isinstance(arg, Splat):
                    ctx.emit(consts.COERCE_ARRAY)
                else:
                    ctx.emit(consts.BUILD_ARRAY, 1)
            for i in range(len(self.args) - 1):
                ctx.emit(consts.SEND, ctx.create_symbol_const("+"), 1)
        else:
            for arg in self.args:
                arg.compile(ctx)
        if self.block_arg is not None:
            self.block_arg.compile(ctx)

        ctx.current_lineno = self.lineno
        symbol = ctx.create_symbol_const(self.method)
        if self.is_splat() and self.block_arg is not None:
            ctx.emit(consts.SEND_BLOCK_SPLAT, symbol)
        elif self.is_splat():
            ctx.emit(consts.SEND_SPLAT, symbol)
        elif self.block_arg is not None:
            ctx.emit(consts.SEND_BLOCK, symbol, len(self.args) + 1)
        else:
            ctx.emit(consts.SEND, symbol, len(self.args))

    def is_splat(self):
        for arg in self.args:
            if isinstance(arg, Splat):
                return True
        return False

    def compile_receiver(self, ctx):
        self.receiver.compile(ctx)
        return 1

    def compile_load(self, ctx):
        ctx.emit(consts.SEND, ctx.create_symbol_const(self.method), 0)

    def compile_store(self, ctx):
        ctx.emit(consts.SEND, ctx.create_symbol_const(self.method + "="), 1)


class Splat(Node):
    def __init__(self, value):
        self.value = value

    def locate_symbols(self, symtable):
        self.value.locate_symbols(symtable)

    def compile(self, ctx):
        self.value.compile(ctx)


class SendBlock(Node):
    def __init__(self, block_args, splat_arg, block):
        self.block_args = block_args
        self.splat_arg = splat_arg
        self.block = block

    def locate_symbols(self, symtable):
        block_symtable = BlockSymbolTable(symtable)
        symtable.add_subscope(self, block_symtable)
        for arg in self.block_args:
            block_symtable.declare_local(arg.name)
        self.block.locate_symbols(block_symtable)

    def compile(self, ctx):
        block_ctx = ctx.get_subctx("block in %s" % ctx.code_name, self)
        for name, kind in block_ctx.symtable.cells.iteritems():
            if kind == block_ctx.symtable.CELLVAR:
                block_ctx.symtable.get_cell_num(name)
        for arg in self.block_args:
            if block_ctx.symtable.is_local(arg.name):
                block_ctx.symtable.get_local_num(arg.name)
            elif block_ctx.symtable.is_cell(arg.name):
                block_ctx.symtable.get_cell_num(arg.name)

        self.block.compile(block_ctx)
        block_ctx.emit(consts.RETURN)
        block_args = [a.name for a in self.block_args]
        bc = block_ctx.create_bytecode(block_args, [], None, None)
        ctx.emit(consts.LOAD_CONST, ctx.create_const(bc))

        cells = [None] * len(block_ctx.symtable.cell_numbers)
        for name, pos in block_ctx.symtable.cell_numbers.iteritems():
            cells[pos] = name
        num_cells = 0
        for i in xrange(len(cells) - 1, -1, -1):
            name = cells[i]
            if block_ctx.symtable.cells[name] == block_ctx.symtable.FREEVAR:
                ctx.emit(consts.LOAD_CLOSURE, ctx.symtable.get_cell_num(name))
                num_cells += 1

        ctx.emit(consts.BUILD_BLOCK, num_cells)


class BlockArgument(Node):
    def __init__(self, value):
        self.value = value

    def locate_symbols(self, symtable):
        self.value.locate_symbols(symtable)

    def compile(self, ctx):
        self.value.compile(ctx)
        ctx.emit(consts.COERCE_BLOCK)


class Subscript(Node):
    def __init__(self, target, args, lineno):
        Node.__init__(self, lineno)
        self.target = target
        self.args = args

    def validate_assignment(self, transformer, node):
        pass

    def locate_symbols(self, symtable):
        self.target.locate_symbols(symtable)
        for arg in self.args:
            arg.locate_symbols(symtable)

    def locate_symbols_assignment(self, symtable):
        self.locate_symbols(symtable)

    def compile(self, ctx):
        Send(self.target, "[]", self.args, None, self.lineno).compile(ctx)

    def compile_receiver(self, ctx):
        self.target.compile(ctx)
        for arg in self.args:
            arg.compile(ctx)
        ctx.emit(consts.BUILD_ARRAY, len(self.args))
        return 2

    def compile_load(self, ctx):
        ctx.emit(consts.SEND_SPLAT, ctx.create_symbol_const("[]"))

    def compile_store(self, ctx):
        ctx.emit(consts.BUILD_ARRAY, 1)
        ctx.emit(consts.SEND, ctx.create_symbol_const("+"), 1)
        ctx.emit(consts.SEND_SPLAT, ctx.create_symbol_const("[]="))


class LookupConstant(Node):
    def __init__(self, value, name, lineno):
        Node.__init__(self, lineno)
        self.value = value
        self.name = name

    def validate_assignment(self, transformer, node):
        pass

    def locate_symbols(self, symtable):
        self.value.locate_symbols(symtable)

    def locate_symbols_assignment(self, symtable):
        self.locate_symbols(symtable)

    def compile(self, ctx):
        if self.name[0].isupper():
            self.value.compile(ctx)
            ctx.current_lineno = self.lineno
            ctx.emit(consts.LOAD_CONSTANT, ctx.create_symbol_const(self.name))
        else:
            Send(self.value, self.name, [], None, self.lineno).compile(ctx)

    def compile_receiver(self, ctx):
        self.value.compile(ctx)
        return 1

    def compile_load(self, ctx):
        ctx.emit(consts.LOAD_CONSTANT, ctx.create_symbol_const(self.name))

    def compile_store(self, ctx):
        ctx.emit(consts.STORE_CONSTANT, ctx.create_symbol_const(self.name))


class Self(Node):
    def locate_symbols(self, symtable):
        pass

    def compile(self, ctx):
        ctx.emit(consts.LOAD_SELF)


class Scope(Node):
    def locate_symbols(self, symtable):
        pass

    def compile(self, ctx):
        ctx.emit(consts.LOAD_SCOPE)


class Variable(Node):
    def __init__(self, name, lineno):
        Node.__init__(self, lineno)
        self.name = name

    def validate_assignment(self, transformer, node):
        if self.name == "__FILE__" or "?" in self.name or "!" in self.name:
            transformer.error(node)

    def locate_symbols(self, symtable):
        if (self.name not in ["true", "false", "nil", "self"] and
            not self.name[0].isupper()):
            symtable.declare_read(self.name)

    def locate_symbols_assignment(self, symtable):
        symtable.declare_write(self.name)

    def compile(self, ctx):
        named_consts = {
            "true": ctx.space.w_true,
            "false": ctx.space.w_false,
            "nil": ctx.space.w_nil,
        }
        if self.name in named_consts:
            ctx.emit(consts.LOAD_CONST, ctx.create_const(named_consts[self.name]))
        elif self.name == "self":
            ctx.emit(consts.LOAD_SELF)
        elif self.name == "__FILE__":
            ctx.emit(consts.LOAD_CODE)
            ctx.emit(consts.SEND, ctx.create_symbol_const("filepath"), 0)
        elif ctx.symtable.is_local(self.name):
            ctx.emit(consts.LOAD_LOCAL, ctx.symtable.get_local_num(self.name))
        elif ctx.symtable.is_cell(self.name):
            ctx.emit(consts.LOAD_DEREF, ctx.symtable.get_cell_num(self.name))
        else:
            Send(Self(self.lineno), self.name, [], None, self.lineno).compile(ctx)

    def compile_receiver(self, ctx):
        return 0

    def compile_load(self, ctx):
        self.compile(ctx)

    def compile_store(self, ctx):
        if ctx.symtable.is_local(self.name):
            loc = ctx.symtable.get_local_num(self.name)
            ctx.emit(consts.STORE_LOCAL, loc)
        elif ctx.symtable.is_cell(self.name):
            loc = ctx.symtable.get_cell_num(self.name)
            ctx.emit(consts.STORE_DEREF, loc)


class Global(Node):
    def __init__(self, name):
        self.name = name

    def validate_assignment(self, transformer, node):
        pass

    def locate_symbols(self, symtable):
        pass

    def locate_symbols_assignment(self, symtable):
        pass

    def compile(self, ctx):
        ctx.emit(consts.LOAD_GLOBAL, ctx.create_symbol_const(self.name))

    def compile_receiver(self, ctx):
        return 0

    def compile_load(self, ctx):
        self.compile(ctx)

    def compile_store(self, ctx):
        ctx.emit(consts.STORE_GLOBAL, ctx.create_symbol_const(self.name))


class InstanceVariable(Node):
    def __init__(self, name):
        self.name = name

    def validate_assignment(self, transformer, node):
        pass

    def locate_symbols(self, symtable):
        pass

    def locate_symbols_assignment(self, symtable):
        pass

    def compile(self, ctx):
        self.compile_receiver(ctx)
        self.compile_load(ctx)

    def compile_receiver(self, ctx):
        ctx.emit(consts.LOAD_SELF)
        return 1

    def compile_load(self, ctx):
        ctx.emit(consts.LOAD_INSTANCE_VAR, ctx.create_symbol_const(self.name))

    def compile_store(self, ctx):
        ctx.emit(consts.STORE_INSTANCE_VAR, ctx.create_symbol_const(self.name))


class ClassVariable(Node):
    def __init__(self, name):
        self.name = name

    def validate_assignment(self, transformer, node):
        pass


class Array(Node):
    def __init__(self, items):
        self.items = items

    def locate_symbols(self, symtable):
        for item in self.items:
            item.locate_symbols(symtable)

    def compile(self, ctx):
        for item in self.items:
            item.compile(ctx)
        ctx.emit(consts.BUILD_ARRAY, len(self.items))


class Hash(Node):
    def __init__(self, items):
        self.items = items

    def locate_symbols(self, symtable):
        for k, v in self.items:
            k.locate_symbols(symtable)
            v.locate_symbols(symtable)

    def compile(self, ctx):
        ctx.emit(consts.BUILD_HASH)
        for k, v in self.items:
            ctx.emit(consts.DUP_TOP)
            k.compile(ctx)
            v.compile(ctx)
            ctx.emit(consts.SEND, ctx.create_symbol_const("[]="), 2)
            ctx.emit(consts.DISCARD_TOP)


class Range(Node):
    def __init__(self, start, stop, inclusive):
        self.start = start
        self.stop = stop
        self.inclusive = inclusive

    def locate_symbols(self, symtable):
        self.start.locate_symbols(symtable)
        self.stop.locate_symbols(symtable)

    def compile(self, ctx):
        self.start.compile(ctx)
        self.stop.compile(ctx)
        if self.inclusive:
            ctx.emit(consts.BUILD_RANGE_INCLUSIVE)
        else:
            ctx.emit(consts.BUILD_RANGE)


class ConstantNode(Node):
    def locate_symbols(self, symtable):
        pass

    def compile(self, ctx):
        ctx.emit(consts.LOAD_CONST, self.create_const(ctx))


class ConstantInt(ConstantNode):
    def __init__(self, intvalue):
        self.intvalue = intvalue

    def create_const(self, ctx):
        return ctx.create_int_const(self.intvalue)


class ConstantFloat(ConstantNode):
    def __init__(self, floatvalue):
        self.floatvalue = floatvalue

    def create_const(self, ctx):
        return ctx.create_float_const(self.floatvalue)


class ConstantSymbol(ConstantNode):
    def __init__(self, symbol):
        self.symbol = symbol

    def create_const(self, ctx):
        return ctx.create_symbol_const(self.symbol)


class ConstantString(ConstantNode):
    def __init__(self, strvalue):
        self.strvalue = strvalue

    def create_const(self, ctx):
        return ctx.create_string_const(self.strvalue)

    def compile(self, ctx):
        ConstantNode.compile(self, ctx)
        ctx.emit(consts.COPY_STRING)


class ConstantRegexp(ConstantNode):
    def __init__(self, regexp):
        self.regexp = regexp

    def create_const(self, ctx):
        return ctx.create_const(ctx.space.newregexp(self.regexp))
