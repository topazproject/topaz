from rupypy.objects.objectobject import W_BaseObject


class W_SymbolObject(W_BaseObject):
    _immutable_fields_ = ["symbol"]

    def __init__(self, symbol):
        self.symbol = symbol

    def symbol_w(self, space):
        return self.symbol