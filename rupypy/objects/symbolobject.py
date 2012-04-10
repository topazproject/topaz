from rupypy.objects.objectobject import W_Object


class W_SymbolObject(W_Object):
    _immutable_fields_ = ["symbol"]

    def __init__(self, symbol):
        self.symbol = symbol

    def symbol_w(self, space):
        return self.symbol