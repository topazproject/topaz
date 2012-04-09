from rupypy.objects.base import W_Object


class W_SymbolObject(W_Object):
    def __init__(self, symbol):
        self.symbol = symbol