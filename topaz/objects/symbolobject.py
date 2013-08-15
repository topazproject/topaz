from topaz.module import ClassDef
from topaz.modules.comparable import Comparable
from topaz.objects.objectobject import W_Object


class W_SymbolObject(W_Object):
    _immutable_fields_ = ["symbol"]
    classdef = ClassDef("Symbol", W_Object.classdef)
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

    @classdef.singleton_method("all_symbols")
    def singleton_method_all_symbols(self, space):
        return space.newarray(space.symbol_cache.values())

    @classdef.method("extend")
    @classdef.method("singleton_class")
    def method_singleton_class(self, space):
        raise space.error(space.w_TypeError, "can't define singleton")

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr(self.symbol)

    @classdef.method("inspect")
    def method_inspect(self, space):
        string_format = (not self.symbol or not self.symbol[0].isalpha() or
            not self.symbol.isalnum())
        if string_format:
            result = [":", '"']
            for c in self.symbol:
                if c == '"':
                    result.append("\\")
                result.append(c)
            result.append('"')
            return space.newstr_fromchars(result)
        else:
            return space.newstr_fromstr(":%s" % self.symbol)

    @classdef.method("length")
    @classdef.method("size")
    def method_size(self, space):
        return space.newint(len(self.symbol))

    @classdef.method("empty?")
    def method_emptyp(self, space):
        return space.newbool(not self.symbol)

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

    @classdef.method("downcase")
    def method_downcase(self, space):
        return space.newsymbol(self.symbol.lower())

    @classdef.method("upcase")
    def method_upcase(self, space):
        return space.newsymbol(self.symbol.upper())
