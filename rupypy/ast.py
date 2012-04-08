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

class BinOp(Node):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

class ConstantInt(Node):
    def __init__(self, intvalue):
        self.invalue = intvalue