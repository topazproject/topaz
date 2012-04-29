from rupypy.objects.objectobject import W_BaseObject


class W_CodeObject(W_BaseObject):
    _immutable_fields_ = ["bytecode"]

    def __init__(self, bytecode):
        self.bytecode = bytecode