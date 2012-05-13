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


class Assignment(Node):
    def __init__(self, oper, target, value, lineno):
        Node.__init__(self, lineno)
        self.oper = oper
        self.target = target
        self.value = value

    def locate_symbols(self, symtable):
        if not self.target[0].isupper():
            symtable.declare_write(self.target)
        self.value.locate_symbols(symtable)

    def compile(self, ctx):
        if self.oper != "=":
            Variable(self.target, self.lineno).compile(ctx)
        self.value.compile(ctx)
        if self.oper != "=":
            ctx.emit(consts.SEND, ctx.create_symbol_const(self.oper[0]), 1)
        if ctx.symtable.is_local(self.target):
            loc = ctx.symtable.get_local_num(self.target)
            ctx.emit(consts.STORE_LOCAL, loc)
        elif ctx.symtable.is_cell(self.target):
            loc = ctx.symtable.get_cell_num(self.target)
            ctx.emit(consts.STORE_DEREF, loc)


class InstanceVariableAssignment(Node):
    def __init__(self, oper, name, value):
        self.oper = oper
        self.name = name
        self.value = value

    def locate_symbols(self, symtable):
        self.value.locate_symbols(symtable)

    def compile(self, ctx):
        ctx.emit(consts.LOAD_SELF)
        if self.oper != "=":
            InstanceVariable(self.name).compile(ctx)
        self.value.compile(ctx)
        if self.oper != "=":
            ctx.emit(consts.SEND, ctx.create_symbol_const(self.oper[0]), 1)
        ctx.emit(consts.STORE_INSTANCE_VAR, ctx.create_symbol_const(self.name))


class MethodAssignment(Node):
    def __init__(self, oper, receiver, name, value):
        self.oper = oper
        self.receiver = receiver
        self.name = name
        self.value = value

    def locate_symbols(self, symtable):
        self.receiver.locate_symbols(symtable)
        self.value.locate_symbols(symtable)

    def compile(self, ctx):
        self.receiver.compile(ctx)
        if self.oper != "=":
            ctx.emit(consts.DUP_TOP)
            ctx.emit(consts.SEND, ctx.create_symbol_const(self.name), 0)
        self.value.compile(ctx)
        if self.oper != "=":
            ctx.emit(consts.SEND, ctx.create_symbol_const(self.oper[0]), 1)
        ctx.emit(consts.SEND, ctx.create_symbol_const(self.name + "="), 1)


class GlobalAssignment(Node):
    def __init__(self, oper, name, value):
        self.oper = oper
        self.name = name
        self.value = value

    def locate_symbols(self, symtable):
        self.value.locate_symbols(symtable)

    def compile(self, ctx):
        if self.oper != "=":
            Global(self.name).compile(ctx)
        self.value.compile(ctx)
        if self.oper != "=":
            ctx.emit(consts.SEND, ctx.create_symbol_const(self.oper[0]), 1)
        ctx.emit(consts.STORE_GLOBAL, ctx.create_symbol_const(self.name))


class ConstantAssignment(Node):
    def __init__(self, oper, receiver, name, value):
        self.oper = oper
        self.receiver = receiver
        self.name = name
        self.value = value

    def locate_symbols(self, symtable):
        self.receiver.locate_symbols(symtable)
        self.value.locate_symbols(symtable)

    def compile(self, ctx):
        self.receiver.compile(ctx)
        if self.oper != "=":
            ctx.emit(consts.DUP_TOP)
            ctx.emit(consts.LOAD_CONSTANT, ctx.create_symbol_const(self.name))
        self.value.compile(ctx)
        if self.oper != "=":
            ctx.emit(consts.SEND, ctx.create_symbol_const(self.oper[0]), 1)
        ctx.emit(consts.STORE_CONSTANT, ctx.create_symbol_const(self.name))


class If(Node):
    def __init__(self, cond, body, elsebody):
        self.cond = cond
        self.body = body
        self.elsebody = elsebody

    def locate_symbols(self, symtable):
        self.cond.locate_symbols(symtable)
        self.body.locate_symbols(symtable)

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

        body_ctx = ctx.get_subctx(self.name, self)
        self.body.compile(body_ctx)
        body_ctx.emit(consts.DISCARD_TOP)
        body_ctx.emit(consts.LOAD_CONST, body_ctx.create_const(body_ctx.space.w_nil))
        body_ctx.emit(consts.RETURN)
        bytecode = body_ctx.create_bytecode([], [], None)

        ctx.emit(consts.LOAD_CONST, ctx.create_const(bytecode))
        ctx.emit(consts.BUILD_CLASS)


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
        bytecode = body_ctx.create_bytecode([], [], None)

        ctx.emit(consts.LOAD_SCOPE)
        ctx.emit(consts.LOAD_CONST, ctx.create_symbol_const(self.name))
        ctx.emit(consts.LOAD_CONST, ctx.create_const(bytecode))
        ctx.emit(consts.BUILD_MODULE)


class Function(Node):
    def __init__(self, parent, name, args, block_arg, body):
        self.parent = parent
        self.name = name
        self.args = args
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
                bc = arg_ctx.create_bytecode([], [], None)
                defaults.append(bc)
        if self.block_arg is not None:
            if function_ctx.symtable.is_local(self.block_arg):
                function_ctx.symtable.get_local_num(self.block_arg)
            elif function_ctx.symtable.is_cell(self.block_arg):
                function_ctx.symtable.get_cell_num(self.block_arg)

        self.body.compile(function_ctx)
        function_ctx.emit(consts.RETURN)
        arg_names = [a.name for a in self.args]
        bytecode = function_ctx.create_bytecode(arg_names, defaults, self.block_arg)

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


class Return(BaseStatement):
    def __init__(self, expr):
        self.expr = expr

    def locate_symbols(self, symtable):
        self.expr.locate_symbols(symtable)

    def compile(self, ctx):
        self.expr.compile(ctx)
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
        Send(self.left, self.op, [self.right], self.lineno).compile(ctx)


class UnaryOp(Node):
    def __init__(self, op, value, lineno):
        Node.__init__(self, lineno)
        self.op = op
        self.value = value

    def locate_symbols(self, symtable):
        self.value.locate_symbols(symtable)

    def compile(self, ctx):
        Send(self.value, self.op + "@", [], self.lineno).compile(ctx)


class Send(Node):
    def __init__(self, receiver, method, args, lineno):
        self.receiver = receiver
        self.method = method
        self.args = args
        self.lineno = lineno

    def convert_to_assignment(self, transformer, node, oper, value):
        # XXX: this will allow self.foo() = 3; which it shouldn't.
        assert not self.args
        return MethodAssignment(oper, self.receiver, self.method, value)

    def locate_symbols(self, symtable):
        self.receiver.locate_symbols(symtable)
        for arg in self.args:
            arg.locate_symbols(symtable)

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
            ctx.current_lineno = self.lineno
            ctx.emit(consts.SEND_SPLAT, ctx.create_symbol_const(self.method))
        else:
            for arg in self.args:
                arg.compile(ctx)
            ctx.current_lineno = self.lineno
            ctx.emit(consts.SEND, ctx.create_symbol_const(self.method), len(self.args))

    def is_splat(self):
        for arg in self.args:
            if isinstance(arg, Splat):
                return True
        return False


class SendBlock(Node):
    def __init__(self, receiver, method, args, block_args, block, lineno):
        Node.__init__(self, lineno)
        self.receiver = receiver
        self.method = method
        self.args = args
        self.block_args = block_args
        self.block = block

    def locate_symbols(self, symtable):
        self.receiver.locate_symbols(symtable)
        for arg in self.args:
            arg.locate_symbols(symtable)

        block_symtable = BlockSymbolTable(symtable)
        symtable.add_subscope(self, block_symtable)
        for arg in self.block_args:
            block_symtable.declare_local(arg.name)
        self.block.locate_symbols(block_symtable)

    def compile(self, ctx):
        self.receiver.compile(ctx)
        for arg in self.args:
            arg.compile(ctx)

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
        bc = block_ctx.create_bytecode(block_args, [], None)

        ctx.current_lineno = self.lineno
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
        ctx.emit(consts.SEND_BLOCK, ctx.create_symbol_const(self.method), len(self.args) + 1)


class Splat(Node):
    def __init__(self, value):
        self.value = value

    def locate_symbols(self, symtable):
        self.value.locate_symbols(symtable)

    def compile(self, ctx):
        self.value.compile(ctx)


class LookupConstant(Node):
    def __init__(self, value, name, lineno):
        Node.__init__(self, lineno)
        self.value = value
        self.name = name

    def convert_to_assignment(self, transformer, node, oper, value):
        return ConstantAssignment(oper, self.value, self.name, value)

    def locate_symbols(self, symtable):
        self.value.locate_symbols(symtable)

    def compile(self, ctx):
        if self.name[0].isupper():
            self.value.compile(ctx)
            ctx.emit(consts.LOAD_CONSTANT, ctx.create_symbol_const(self.name))
        else:
            Send(self.value, self.name, [], self.lineno).compile(ctx)


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

    def convert_to_assignment(self, transormer, node, oper, value):
        if self.name == "__FILE__" or "?" in self.name:
            transormer.error(node)
        return Assignment(oper, self.name, value, node.getsourcepos().lineno)

    def locate_symbols(self, symtable):
        if (self.name not in ["true", "false", "nil", "self"] and
            not self.name[0].isupper()):
            symtable.declare_read(self.name)

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
            Send(Self(self.lineno), self.name, [], self.lineno).compile(ctx)


class Global(Node):
    def __init__(self, name):
        self.name = name

    def convert_to_assignment(self, transormer, node, oper, value):
        return GlobalAssignment(oper, self.name, value)

    def locate_symbols(self, symtable):
        pass

    def compile(self, ctx):
        ctx.emit(consts.LOAD_GLOBAL, ctx.create_symbol_const(self.name))


class InstanceVariable(Node):
    def __init__(self, name):
        self.name = name

    def convert_to_assignment(self, transormer, node, oper, value):
        return InstanceVariableAssignment(oper, self.name, value)

    def locate_symbols(self, symtable):
        pass

    def compile(self, ctx):
        ctx.emit(consts.LOAD_SELF)
        ctx.emit(consts.LOAD_INSTANCE_VAR, ctx.create_symbol_const(self.name))


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