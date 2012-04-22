from pypy.rlib.objectmodel import we_are_translated

from rupypy import consts
from rupypy.compiler import CompilerContext, SymbolTable, BlockSymbolTable


class Node(object):
    _attrs_ = []

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
            stmts = [Statement(Variable("nil"))]
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
    def __init__(self, oper, target, value):
        self.oper = oper
        self.target = target
        self.value = value

    def locate_symbols(self, symtable):
        if not self.target[0].isupper():
            symtable.declare_write(self.target)
        self.value.locate_symbols(symtable)

    def compile(self, ctx):
        if self.oper != "=":
            Variable(self.target).compile(ctx)
        self.value.compile(ctx)
        if self.oper != "=":
            ctx.emit(consts.SEND, ctx.create_symbol_const(self.oper[0]), 1)
        if self.target[0].isupper():
            ctx.emit(consts.STORE_CONSTANT, ctx.create_symbol_const(self.target))
        else:
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
        if self.oper != "=":
            InstanceVariable(self.name).compile(ctx)
        self.value.compile(ctx)
        if self.oper != "=":
            ctx.emit(consts.SEND, ctx.create_symbol_const(self.oper[0]), 1)
        ctx.emit(consts.LOAD_SELF)
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

class If(Node):
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

    def locate_symbols(self, symtable):
        self.cond.locate_symbols(symtable)
        self.body.locate_symbols(symtable)

    def compile(self, ctx):
        self.cond.compile(ctx)
        pos = ctx.get_pos()
        ctx.emit(consts.JUMP_IF_FALSE, 0)
        self.body.compile(ctx)
        else_pos = ctx.get_pos()
        ctx.emit(consts.JUMP, 0)
        ctx.patch_jump(pos)
        ctx.emit(consts.LOAD_CONST, ctx.create_const(ctx.space.w_nil))
        ctx.patch_jump(else_pos)

class While(Node):
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

    def locate_symbols(self, symtable):
        self.cond.locate_symbols(symtable)
        self.body.locate_symbols(symtable)

    def compile(self, ctx):
        start_pos = ctx.get_pos()
        self.cond.compile(ctx)
        jump_pos = ctx.get_pos()
        ctx.emit(consts.JUMP_IF_FALSE, 0)
        self.body.compile(ctx)
        # The body leaves an extra item on the stack, discard it.
        ctx.emit(consts.DISCARD_TOP)
        ctx.emit(consts.JUMP, start_pos)
        ctx.patch_jump(jump_pos)
        # For now, while always returns a nil, eventually it can also return a
        # value from a break
        ctx.emit(consts.LOAD_CONST, ctx.create_const(ctx.space.w_nil))

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
        ctx.emit(consts.LOAD_SELF)
        ctx.emit(consts.LOAD_CONST, ctx.create_symbol_const(self.name))
        if self.superclass is None:
            ctx.emit(consts.LOAD_CONST, ctx.create_const(ctx.space.w_nil))
        else:
            self.superclass.compile(ctx)

        body_symtable = ctx.symtable.get_subscope(self)
        body_ctx = CompilerContext(ctx.space, body_symtable)
        self.body.compile(body_ctx)
        body_ctx.emit(consts.DISCARD_TOP)
        body_ctx.emit(consts.LOAD_CONST, body_ctx.create_const(body_ctx.space.w_nil))
        body_ctx.emit(consts.RETURN)
        bytecode = body_ctx.create_bytecode([])

        ctx.emit(consts.LOAD_CONST, ctx.create_const(ctx.space.newcode(bytecode)))
        ctx.emit(consts.BUILD_CLASS)

class Function(Node):
    def __init__(self, name, args, body):
        self.name = name
        self.args = args
        self.body = body

    def locate_symbols(self, symtable):
        body_symtable = SymbolTable()
        symtable.add_subscope(self, body_symtable)
        for name in self.args:
            body_symtable.declare_local(name)
        self.body.locate_symbols(body_symtable)

    def compile(self, ctx):
        function_symtable = ctx.symtable.get_subscope(self)
        function_ctx = CompilerContext(ctx.space, function_symtable)
        self.body.compile(function_ctx)
        function_ctx.emit(consts.RETURN)
        bytecode = function_ctx.create_bytecode(self.args)

        ctx.emit(consts.LOAD_SELF)
        ctx.emit(consts.LOAD_CONST, ctx.create_symbol_const(self.name))
        ctx.emit(consts.LOAD_CONST, ctx.create_const(ctx.space.newcode(bytecode)))
        ctx.emit(consts.DEFINE_FUNCTION)


class Return(BaseStatement):
    def __init__(self, expr):
        self.expr = expr

    def locate_symbols(self, symtable):
        self.expr.locate_symbols(symtable)

    def compile(self, ctx):
        self.expr.compile(ctx)
        ctx.emit(consts.RETURN)

class Yield(Node):
    def __init__(self, args):
        self.args = args

    def locate_symbols(self, symtable):
        for arg in self.args:
            arg.locate_symbols(symtable)

    def compile(self, ctx):
        for arg in self.args:
            arg.compile(ctx)
        ctx.emit(consts.YIELD, len(self.args))

class BinOp(Node):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def locate_symbols(self, symtable):
        self.left.locate_symbols(symtable)
        self.right.locate_symbols(symtable)

    def compile(self, ctx):
        Send(self.left, self.op, [self.right]).compile(ctx)

class Send(Node):
    def __init__(self, receiver, method, args):
        self.receiver = receiver
        self.method = method
        self.args = args

    def convert_to_assignment(self, oper, value):
        # XXX: this will allow self.foo() = 3; which it shouldn't.
        assert not self.args
        return MethodAssignment(oper, self.receiver, self.method, value)

    def locate_symbols(self, symtable):
        self.receiver.locate_symbols(symtable)
        for arg in self.args:
            arg.locate_symbols(symtable)

    def compile(self, ctx):
        self.receiver.compile(ctx)
        for i in range(len(self.args) - 1, -1, -1):
            self.args[i].compile(ctx)
        ctx.emit(consts.SEND, ctx.create_symbol_const(self.method), len(self.args))

class SendBlock(Node):
    def __init__(self, receiver, method, args, block_args, block):
        self.receiver = receiver
        self.method = method
        self.args = args
        self.block_args = block_args
        self.block = block

    def locate_symbols(self, symtable):
        for arg in self.args:
            arg.locate_symbols(symtable)

        block_symtable = BlockSymbolTable(symtable)
        symtable.add_subscope(self, block_symtable)
        for arg in self.block_args:
            block_symtable.declare_local(arg)
        self.block.locate_symbols(block_symtable)

    def compile(self, ctx):
        self.receiver.compile(ctx)
        for i in range(len(self.args) - 1, -1, -1):
            self.args[i].compile(ctx)

        block_symtable = ctx.symtable.get_subscope(self)
        block_ctx = CompilerContext(ctx.space, block_symtable)
        self.block.compile(block_ctx)
        block_ctx.emit(consts.RETURN)
        bc = block_ctx.create_bytecode(self.block_args)
        ctx.emit(consts.LOAD_CONST, ctx.create_const(ctx.space.newcode(bc)))
        # XXX: order!
        for name in block_symtable.cells:
            ctx.emit(consts.LOAD_CLOSURE, ctx.symtable.get_cell_num(name))
        ctx.emit(consts.BUILD_BLOCK, len(block_symtable.cells))
        ctx.emit(consts.SEND_BLOCK, ctx.create_symbol_const(self.method), len(self.args) + 1)

class Self(Node):
    def locate_symbols(self, symtable):
        pass

    def compile(self, ctx):
        ctx.emit(consts.LOAD_SELF)

class Variable(Node):
    def __init__(self, name):
        self.name = name

    def convert_to_assignment(self, oper, value):
        return Assignment(oper, self.name, value)

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
        elif ctx.symtable.is_local(self.name):
            ctx.emit(consts.LOAD_LOCAL, ctx.symtable.get_local_num(self.name))
        elif ctx.symtable.is_cell(self.name):
            ctx.emit(consts.LOAD_DEREF, ctx.symtable.get_cell_num(self.name))
        elif self.name[0].isupper():
            ctx.emit(consts.LOAD_CONSTANT, ctx.create_symbol_const(self.name))
        else:
            Send(Self(), self.name, []).compile(ctx)

class InstanceVariable(Node):
    def __init__(self, name):
        self.name = name

    def convert_to_assignment(self, oper, value):
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