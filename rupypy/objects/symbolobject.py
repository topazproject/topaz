from rupypy.module import ClassDef
from rupypy.modules.comparable import Comparable
from rupypy.objects.objectobject import W_BaseObject

class W_SymbolObject(W_BaseObject):
    _immutable_fields_ = ["symbol"]
    classdef = ClassDef("Symbol", W_BaseObject.classdef)
    classdef.include_module(Comparable)

    def __init__(self, symbol):
        self.symbol = symbol

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
