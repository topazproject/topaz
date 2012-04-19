from rupypy.objects.objectobject import W_BaseObject


class W_BlockObject(W_BaseObject):
    def __init__(self, bytecode, w_self, cells, block):
        self.bytecode = bytecode
        self.w_self = w_self
        self.cells = cells
        self.block = block
