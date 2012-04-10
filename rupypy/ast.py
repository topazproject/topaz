from pypy.rlib.objectmodel import we_are_translated

from rupypy import consts


class Node(object):
    _attrs_ = []

    def __eq__(self, other):
        if not isinstance(other, Node):
            return NotImplemented
        return type(self) is type(other) and self.__dict__ == other.__dict__

    def compile(self, ctx):
        if we_are_translated():
            raise NotImplementedError
        else:
            raise NotImplementedError(type(self).__name__)

class Main(Node):
    def __init__(self, block):
        self.block = block

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

    def compile(self, ctx):
        for idx, stmt in enumerate(self.stmts):
            stmt.compile(ctx)

class Statement(Node):
    def __init__(self, expr):
        self.expr = expr
        self.dont_pop = False

    def compile(self, ctx):
        self.expr.compile(ctx)
        if not self.dont_pop:
            ctx.emit(consts.DISCARD_TOP)

class Assignment(Node):
    def __init__(self, target, value):
        self.target = target
        self.value = value

    def compile(self, ctx):
        loc = ctx.create_local(self.target)
        self.value.compile(ctx)
        ctx.emit(consts.STORE_LOCAL, loc)

class If(Node):
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

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

class BinOp(Node):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def compile(self, ctx):
        Send(self.left, self.op, [self.right]).compile(ctx)

class Send(Node):
    def __init__(self, receiver, method, args):
        self.receiver = receiver
        self.method = method
        self.args = args

    def compile(self, ctx):
        self.receiver.compile(ctx)
        for i in range(len(self.args) - 1, -1, -1):
            self.args[i].compile(ctx)
        ctx.emit(consts.SEND, ctx.create_symbol_const(self.method), len(self.args))

class Self(Node):
    def compile(self, ctx):
        ctx.emit(consts.LOAD_SELF)

class Variable(Node):
    def __init__(self, name):
        self.name = name

    def compile(self, ctx):
        named_consts = {
            "true": ctx.space.w_true,
            "false": ctx.space.w_false,
            "nil": ctx.space.w_nil,
        }
        if self.name in named_consts:
            ctx.emit(consts.LOAD_CONST, ctx.create_const(named_consts[self.name]))
        elif ctx.local_defined(self.name):
            ctx.emit(consts.LOAD_LOCAL, ctx.create_local(self.name))
        else:
            Send(Self(), self.name, []).compile(ctx)

class ConstantInt(Node):
    def __init__(self, intvalue):
        self.intvalue = intvalue

    def compile(self, ctx):
        ctx.emit(consts.LOAD_CONST, ctx.create_int_const(self.intvalue))