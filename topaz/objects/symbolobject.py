from topaz.module import ClassDef
from topaz.modules.comparable import Comparable
from topaz.objects.objectobject import W_Object


class W_SymbolObject(W_Object):
    _immutable_fields_ = ["symbol"]
    classdef = ClassDef("Symbol", W_Object.classdef, filepath=__file__)
    classdef.include_module(Comparable)

    def __init__(self, space, symbol):
        W_Object.__init__(self, space)
        self.symbol = symbol

    def __deepcopy__(self, memo):
        obj = super(W_SymbolObject, self).__deepcopy__(memo)
        obj.symbol = self.symbol
        return obj

    def symbol_w(self, space):
        return self.symbol

    def str_w(self, space):
        return self.symbol

    def getsingletonclass(self, space):
        raise space.error(space.w_TypeError, "can't define singleton")

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr(self.symbol)

    @classdef.method("inspect")
    def method_inspect(self, space):
        return space.newstr_fromstr(":%s" % self.symbol)

    @classdef.method("<=>")
    def method_comparator(self, space, w_other):
        if not space.is_kind_of(w_other, space.w_symbol):
            return space.w_nil
        s1 = self.symbol
        s2 = space.symbol_w(w_other)
        if s1 < s2:
            return space.newint(-1)
        elif s1 == s2:
            return space.newint(0)
        elif s1 > s2:
            return space.newint(1)
