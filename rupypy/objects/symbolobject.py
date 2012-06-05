from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_BaseObject

class W_SymbolObject(W_BaseObject):
    _immutable_fields_ = ["symbol"]
    classdef = ClassDef("Symbol", W_BaseObject.classdef)

    def __init__(self, symbol):
        self.symbol = symbol

    def __eq__(self, other):
        return type(self) == type(other) and self.__hash__() == other.__hash__()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self.symbol.__hash__()

    def symbol_w(self, space):
        return self.symbol

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr(self.symbol)

    @classdef.method("<=>", other="symbol")
    def method_comparator(self, space, other):
        s1 = self.symbol
        s2 = other
        if s1 < s2:
            return space.newint(-1)
        elif s1 == s2:
            return space.newint(0)
        elif s1 > s2:
            return space.newint(1)
