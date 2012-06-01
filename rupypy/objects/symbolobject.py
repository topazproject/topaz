from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_BaseObject

class W_SymbolObject(W_BaseObject):
    _immutable_fields_ = ["symbol"]
    classdef = ClassDef("Symbol", W_BaseObject.classdef)

    def __init__(self, symbol):
        self.symbol = symbol

    def symbol_w(self, space):
        return self.symbol

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr(self.symbol)