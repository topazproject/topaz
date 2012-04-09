from rupypy import consts


class Node(object):
    _attrs_ = []

    def __eq__(self, other):
        if not isinstance(other, Node):
            return NotImplemented
        return type(self) is type(other) and self.__dict__ == other.__dict__

    def compile(self, ctx):
        raise NotImplementedError(type(self).__name__)

class Main(Node):
    def __init__(self, block):
        self.block = block

    def compile(self, ctx):
        self.block.compile(ctx)
        ctx.emit(consts.LOAD_CONST, ctx.create_const(ctx.space.newbool(True)))
        ctx.emit(consts.RETURN)

class Block(Node):
    def __init__(self, stmts):
        self.stmts = stmts

    def compile(self, ctx):
        for stmt in self.stmts:
            stmt.compile(ctx)

class Statement(Node):
    def __init__(self, expr):
        self.expr = expr

    def compile(self, ctx):
        self.expr.compile(ctx)
        ctx.emit(consts.DISCARD_TOP)

class Assignment(Node):
    def __init__(self, target, value):
        self.target = target
        self.value = value

class BinOp(Node):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

class Send(Node):
    def __init__(self, receiver, method, args):
        self.receiver = receiver
        self.method = method
        self.args = args

class Self(Node):
    pass

class Variable(Node):
    def __init__(self, name):
        self.name = name

class ConstantInt(Node):
    def __init__(self, intvalue):
        self.intvalue = intvalue

    def compile(self, ctx):
        ctx.emit(consts.LOAD_CONST, ctx.create_int_const(self.intvalue))