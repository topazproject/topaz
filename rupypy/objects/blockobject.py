from rupypy.objects.objectobject import W_BaseObject


class W_BlockObject(W_BaseObject):
    def __init__(self, bytecode, w_self, w_scope, cells, block, parent_interp):
        self.bytecode = bytecode
        self.w_self = w_self
        self.w_scope = w_scope
        self.cells = cells
        self.block = block
        self.parent_interp = parent_interp
