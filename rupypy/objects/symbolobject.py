from rupypy.module import ClassDef
from rupypy.modules.comparable import Comparable
from rupypy.objects.objectobject import W_Object, W_BuiltinObject
from rupypy.objects.exceptionobject import W_TypeError

class W_SymbolObject(W_BuiltinObject):
    _immutable_fields_ = ["symbol"]
    classdef = ClassDef("Symbol", W_Object.classdef)
    classdef.include_module(Comparable)

    def __init__(self, space, symbol):
        W_BuiltinObject.__init__(self, space)
        self.symbol = symbol
        # Optimization: the class won't change, singleton classes are disallowed for symbols
        self.klass = space.getclassobject(self.classdef)

    def symbol_w(self, space):
        return self.symbol

    def getsingletonclass(self, space):
        space.raise_(space.getclassfor(W_TypeError), "can't define singleton")

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
