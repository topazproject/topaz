from rupypy.objects.objectobject import W_Object


class W_CodeObject(W_Object):
    def __init__(self, bytecode):
        self.bytecode = bytecode