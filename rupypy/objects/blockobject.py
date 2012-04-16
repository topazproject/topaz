from rupypy.objects.objectobject import W_BaseObject


class W_BlockObject(W_BaseObject):
    def __init__(self, bytecode, cells):
        self.bytecode = bytecode
        self.cells = cells
