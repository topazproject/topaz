from rupypy.objects.objectobject import W_BaseObject


class W_CodeObject(W_BaseObject):
    def __init__(self, bytecode):
        self.bytecode = bytecode