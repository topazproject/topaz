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
    @classdef.method("id2name")
    def method_to_s(self, space):
        return space.newstr_fromstr(self.symbol)

    @classdef.method("<=>")
    def method_comparator(self, space, w_other):
        assert isinstance(w_other, W_SymbolObject)
        s1 = self.method_to_s(space)
        s2 = w_other.method_to_s(space)
        return s1.method_comparator(space, s2)

    @classdef.method("[]")
    def method_subscript(self, space, w_idx):
        return self.method_to_s(space).method_subscript(space, w_idx)

    @classdef.method("length")
    def method_length(self, space):
        return self.method_to_s(space).method_length(space)

    @classdef.singleton_method("all_symbols")
    def method_all_symbols(self, space):
        return space.newarray(space.symbol_cache.values())
