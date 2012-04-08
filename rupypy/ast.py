class Node(object):
    _attrs_ = []

    def __eq__(self, other):
        if not isinstance(other, Node):
            return NotImplemented
        return type(self) is type(other) and self.__dict__ == other.__dict__

class Block(Node):
    def __init__(self, stmts):
        self.stmts = stmts

class Statement(Node):
    def __init__(self, expr):
        self.expr = expr

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
        self.invalue = intvalue