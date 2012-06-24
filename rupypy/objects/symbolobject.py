from rupypy.module import ClassDef
from rupypy.modules.comparable import Comparable
from rupypy.objects.objectobject import W_Object
from rupypy.objects.exceptionobject import W_TypeError


class W_SymbolObject(W_Object):
    _immutable_fields_ = ["symbol"]
    classdef = ClassDef("Symbol", W_Object.classdef)
    classdef.include_module(Comparable)

    def __init__(self, space, symbol):
        W_Object.__init__(self, space)
        self.symbol = symbol

    def symbol_w(self, space):
        return self.symbol

    def getsingletonclass(self, space):
        space.raise_(space.getclassfor(W_TypeError), "can't define singleton")

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
