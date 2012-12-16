import copy

from pypy.rlib import jit
from pypy.rlib.objectmodel import newlist_hint, compute_hash
from pypy.rlib.rarithmetic import intmask, ovfcheck
from pypy.rlib.rbigint import rbigint
from pypy.rlib.rerased import new_static_erasing_pair

from rupypy.module import ClassDef
from rupypy.modules.comparable import Comparable
from rupypy.objects.objectobject import W_Object
from rupypy.utils.formatting import StringFormatter


def create_trans_table(source, replacement, inv=False):
    src = expand_trans_str(source, len(source), inv)
    repl = expand_trans_str(replacement, len(src))
    table = [chr(i) for i in xrange(256)]
    for i, c in enumerate(src):
        table[ord(c)] = repl[i]
    return table


def expand_trans_str(source, res_len, inv=False):
    # check the source for range definitions
    # and insert the missing characters
    expanded_source = []
    char = ""
    for i in range(res_len):
        if i < len(source):
            char = source[i]
        if char == "-":
            # expand the range
            assert 0 < i < len(source) - 1
            range_beg = ord(source[i - 1])
            range_end = ord(source[i + 1])
            for j in range(range_beg + 1, range_end - 1):
                expanded_source.append(chr(j))
        elif char:
            expanded_source.append(char[0])

    if inv:
        inverted_source = []
        # invert the source
        for i in range(256):
            if chr(i) not in expanded_source:
                inverted_source.append(chr(i))
        return inverted_source

    return expanded_source


class StringStrategy(object):
    def __init__(self, space):
        pass

    def __deepcopy__(self, memo):
        memo[id(self)] = result = object.__new__(self.__class__)
        return result


class ConstantStringStrategy(StringStrategy):
    erase, unerase = new_static_erasing_pair("constant")

    def str_w(self, storage):
        return self.unerase(storage)

    def liststr_w(self, storage):
        strvalue = self.unerase(storage)
        return [c for c in strvalue]

    def length(self, storage):
        return len(self.unerase(storage))

    def getitem(self, storage, idx):
        return self.unerase(storage)[idx]

    def getslice(self, space, storage, start, end):
        return space.newstr_fromstr(self.unerase(storage)[start:end])

    def hash(self, storage):
        return compute_hash(self.unerase(storage))

    def copy(self, space, storage):
        return W_StringObject(space, storage, self)

    def to_mutable(self, space, s):
        s.strategy = strategy = space.fromcache(MutableStringStrategy)
        s.str_storage = strategy.erase(self.liststr_w(s.str_storage))

    def extend_into(self, src_storage, dst_storage):
        dst_storage += self.unerase(src_storage)

    def mul(self, space, storage, times):
        return space.newstr_fromstr(self.unerase(storage) * times)


class MutableStringStrategy(StringStrategy):
    erase, unerase = new_static_erasing_pair("mutable")

    def str_w(self, storage):
        return "".join(self.unerase(storage))

    def liststr_w(self, storage):
        return self.unerase(storage)

    def length(self, storage):
        return len(self.unerase(storage))

    def getitem(self, storage, idx):
        return self.unerase(storage)[idx]

    def getslice(self, space, storage, start, end):
        return space.newstr_fromchars(self.unerase(storage)[start:end])

    def hash(self, storage):
        storage = self.unerase(storage)
        length = len(storage)
        if length == 0:
            return -1
        x = ord(storage[0]) << 7
        i = 0
        while i < length:
            x = intmask((1000003 * x) ^ ord(storage[i]))
            i += 1
        x ^= length
        return intmask(x)

    def copy(self, space, storage):
        return W_StringObject(space, storage, self)

    def to_mutable(self, space, s):
        pass

    def extend_into(self, src_storage, dst_storage):
        dst_storage += self.unerase(src_storage)

    def clear(self, s):
        storage = self.unerase(s.str_storage)
        del storage[:]

    def mul(self, space, storage, times):
        return space.newstr_fromchars(self.unerase(storage) * times)

    def downcase(self, storage):
        storage = self.unerase(storage)
        changed = False
        for i, c in enumerate(storage):
            new_c = c.lower()
            changed |= (c != new_c)
            storage[i] = new_c
        return changed


class W_StringObject(W_Object):
    classdef = ClassDef("String", W_Object.classdef, filepath=__file__)
    classdef.include_module(Comparable)

    def __init__(self, space, storage, strategy):
        W_Object.__init__(self, space)
        self.str_storage = storage
        self.strategy = strategy

    def __deepcopy__(self, memo):
        obj = super(W_StringObject, self).__deepcopy__(memo)
        obj.str_storage = copy.deepcopy(self.str_storage, memo)
        obj.strategy = copy.deepcopy(self.strategy, memo)
        return obj

    @staticmethod
    def newstr_fromstr(space, strvalue):
        strategy = space.fromcache(ConstantStringStrategy)
        storage = strategy.erase(strvalue)
        return W_StringObject(space, storage, strategy)

    @staticmethod
    @jit.look_inside_iff(lambda space, strs_w: jit.isconstant(len(strs_w)))
    def newstr_fromstrs(space, strs_w):
        total_length = 0
        for w_item in strs_w:
            assert isinstance(w_item, W_StringObject)
            total_length += w_item.length()

        storage = newlist_hint(total_length)
        for w_item in strs_w:
            assert isinstance(w_item, W_StringObject)
            w_item.strategy.extend_into(w_item.str_storage, storage)
        return space.newstr_fromchars(storage)

    @staticmethod
    def newstr_fromchars(space, chars):
        strategy = space.fromcache(MutableStringStrategy)
        storage = strategy.erase(chars)
        return W_StringObject(space, storage, strategy)

    def str_w(self, space):
        return self.strategy.str_w(self.str_storage)

    def liststr_w(self, space):
        return self.strategy.liststr_w(self.str_storage)

    def length(self):
        return self.strategy.length(self.str_storage)

    def copy(self, space):
        return self.strategy.copy(space, self.str_storage)

    def replace(self, space, chars):
        strategy = space.fromcache(MutableStringStrategy)
        self.str_storage = strategy.erase(chars)
        self.strategy = strategy

    def extend(self, space, w_other):
        self.strategy.to_mutable(space, self)
        strategy = self.strategy
        assert isinstance(strategy, MutableStringStrategy)
        storage = strategy.unerase(self.str_storage)
        w_other.strategy.extend_into(w_other.str_storage, storage)

    def clear(self, space):
        self.strategy.to_mutable(space, self)
        self.strategy.clear(self)

    def tr_trans(self, space, source, replacement, squeeze):
        change_made = False
        string = space.str_w(self)
        new_string = []
        is_negative_set = len(source) > 1 and source[0] == "^"
        if is_negative_set:
            source = source[1:]

        trans_table = create_trans_table(source, replacement, is_negative_set)

        if squeeze:
            last_repl = ""
            for char in string:
                repl = trans_table[ord(char)]
                if last_repl == repl:
                    continue
                if repl != char:
                    last_repl = repl
                    if not change_made:
                        change_made = True
                new_string.append(repl)
        else:
            for char in string:
                repl = trans_table[ord(char)]
                if not change_made and repl != char:
                    change_made = True
                new_string.append(repl)

        return new_string if change_made else None

    @classdef.method("to_str")
    @classdef.method("to_s")
    def method_to_s(self, space):
        return self

    @classdef.method("inspect")
    def method_inspect(self, space):
        return space.newstr_fromstr('"%s"' % self.str_w(space))

    @classdef.method("+")
    def method_plus(self, space, w_other):
        assert isinstance(w_other, W_StringObject)
        total_size = self.length() + w_other.length()
        s = space.newstr_fromchars(newlist_hint(total_size))
        s.extend(space, self)
        s.extend(space, w_other)
        return s

    @classdef.method("*", times="int")
    def method_times(self, space, times):
        return self.strategy.mul(space, self.str_storage, times)

    @classdef.method("<<")
    def method_lshift(self, space, w_other):
        assert isinstance(w_other, W_StringObject)
        self.extend(space, w_other)
        return self

    @classdef.method("size")
    @classdef.method("length")
    def method_length(self, space):
        return space.newint(self.length())

    @classdef.method("hash")
    def method_hash(self, space):
        return space.newint(self.strategy.hash(self.str_storage))

    @classdef.method("[]")
    def method_subscript(self, space, w_idx, w_count=None):
        start, end, as_range, nil = space.subscript_access(self.length(), w_idx, w_count=w_count)
        if nil:
            return space.w_nil
        elif as_range:
            assert start >= 0
            assert end >= 0
            return self.strategy.getslice(space, self.str_storage, start, end)
        else:
            return space.newstr_fromstr(self.strategy.getitem(self.str_storage, start))

    @classdef.method("<=>")
    def method_comparator(self, space, w_other):
        if isinstance(w_other, W_StringObject):
            s1 = space.str_w(self)
            s2 = space.str_w(w_other)
            if s1 < s2:
                return space.newint(-1)
            elif s1 == s2:
                return space.newint(0)
            elif s1 > s2:
                return space.newint(1)
        else:
            if space.respond_to(w_other, space.newsymbol("to_str")) and space.respond_to(w_other, space.newsymbol("<=>")):
                tmp = space.send(w_other, space.newsymbol("<=>"), [self])
                if tmp is not space.w_nil:
                    return space.newint(-space.int_w(tmp))
            return space.w_nil

    classdef.app_method("""
    def eql? other
        if !other.kind_of?(String)
            false
        else
            self == other
        end
    end
    """)

    @classdef.method("freeze")
    def method_freeze(self, space):
        pass

    @classdef.method("dup")
    def method_dup(self, space):
        return self.copy(space)

    @classdef.method("to_sym")
    @classdef.method("intern")
    def method_to_sym(self, space):
        return space.newsymbol(space.str_w(self))

    @classdef.method("clear")
    def method_clear(self, space):
        self.clear(space)
        return self

    @classdef.method("ljust", integer="int", padstr="str")
    def method_ljust(self, space, integer, padstr=" "):
        if not padstr:
            raise space.error(space.w_ArgumentError, "zero width padding")
        elif integer <= self.length():
            return self.copy(space)
        else:
            pad_len = integer - self.length() - 1
            assert pad_len >= 0
            chars = []
            chars += space.str_w(self)
            for i in xrange(pad_len / len(padstr)):
                chars += padstr
            chars += padstr[:pad_len % len(padstr) + 1]
            return space.newstr_fromchars(chars)

    @classdef.method("split", limit="int")
    def method_split(self, space, w_sep=None, limit=-1):
        if w_sep is None:
            sep = None
        elif isinstance(w_sep, W_StringObject):
            sep = space.str_w(w_sep)
        else:
            raise NotImplementedError("Regexp separators for String#split")
        results = space.str_w(self).split(sep, limit - 1)
        return space.newarray([space.newstr_fromstr(s) for s in results])

    classdef.app_method("""
    def downcase
        copy = self.dup
        copy.downcase!
        return copy
    end
    """)

    @classdef.method("downcase!")
    def method_downcase_i(self, space):
        self.strategy.to_mutable(space, self)
        changed = self.strategy.downcase(self.str_storage)
        return self if changed else space.w_nil

    def _digits(self, s, i, radix):
        number_seen = False
        while i < len(s):
            c = ord(s[i])
            if c == ord("_") and number_seen:
                i += 1
                continue
            if ord("a") <= c <= ord("z"):
                digit = c - ord("a") + 10
            elif ord("A") <= c <= ord("Z"):
                digit = c - ord("A") + 10
            elif ord("0") <= c <= ord("9"):
                digit = c - ord("0")
            else:
                break
            if digit >= radix:
                break
            number_seen = True
            yield digit
            i += 1

    def to_int(self, s, neg, i, radix):
        val = 0
        for digit in self._digits(s, i, radix):
            val = ovfcheck(val * radix + digit)
        if neg:
            val = -val
        return val

    def to_bigint(self, s, neg, i, radix):
        val = rbigint.fromint(0)
        bigint_radix = rbigint.fromint(radix)
        for digit in self._digits(s, i, radix):
            val = val.mul(bigint_radix).add(rbigint.fromint(digit))
        if neg:
            val = val.neg()
        return val

    @classdef.method("to_i", radix="int")
    def method_to_i(self, space, radix=10):
        if not 2 <= radix <= 36:
            raise space.error(space.w_ArgumentError, "invalid radix %d" % radix)
        s = space.str_w(self)
        i = 0
        while i < len(s):
            if not s[i].isspace():
                break
            i += 1
        neg = i < len(s) and s[i] == "-"
        if neg:
            i += 1
        try:
            value = self.to_int(s, neg, i, radix)
        except OverflowError:
            value = self.to_bigint(s, neg, i, radix)
            return space.newbigint_fromrbigint(value)
        else:
            return space.newint(value)

    @classdef.method("tr", source="str", replacement="str")
    def method_tr(self, space, source, replacement):
        string = self.copy(space)
        new_string = self.tr_trans(space, source, replacement, False)
        return space.newstr_fromchars(new_string) if new_string else string

    @classdef.method("tr!", source="str", replacement="str")
    def method_tr_i(self, space, source, replacement):
        new_string = self.tr_trans(space, source, replacement, False)
        self.replace(space, new_string)
        return self if new_string else space.w_nil

    @classdef.method("tr_s", source="str", replacement="str")
    def method_tr_s(self, space, source, replacement):
        string = self.copy(space)
        new_string = self.tr_trans(space, source, replacement, True)
        return space.newstr_fromchars(new_string) if new_string else string

    @classdef.method("tr_s!", source="str", replacement="str")
    def method_tr_s_i(self, space, source, replacement):
        new_string = self.tr_trans(space, source, replacement, True)
        self.replace(space, new_string)
        return self if new_string else space.w_nil

    classdef.app_method("""
    def empty?
        self.length == 0
    end

    def =~(obj)
        case obj
        when String
            raise TypeError, "type mismatch: String given"
        else
            return obj =~ self
        end
    end

    def match(pattern)
        return Regexp.new(pattern).match(self)
    end
    """)

    @classdef.method("%")
    def method_mod(self, space, w_arg):
        if space.is_kind_of(w_arg, space.w_array):
            args_w = space.listview(w_arg)
        else:
            args_w = [w_arg]
        elements_w = StringFormatter(space.str_w(self), args_w).format(space)
        return space.newstr_fromstrs(elements_w)
