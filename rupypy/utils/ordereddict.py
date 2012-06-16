from collections import OrderedDict as PyOrderedDict

from pypy.annotation import model
from pypy.annotation.bookkeeper import getbookkeeper
from pypy.rlib.rarithmetic import r_uint, intmask, LONG_BIT
from pypy.rpython.extregistry import ExtRegistryEntry
from pypy.rpython.lltypesystem import lltype
from pypy.rpython.rmodel import Repr
from pypy.tool.pairtype import pairtype


class OrderedDict(object):
    def __init__(self, eq_func=None, hash_func=None):
        self.contents = PyOrderedDict()
        self.eq_func = eq_func
        self.hash_func = hash_func

    def __getitem__(self, key):
        return self.contents[self._key(key)]

    def __setitem__(self, key, value):
        self.contents[self._key(key)] = value

    def _key(self, key):
        if self.eq_func and self.hash_func:
            return DictKey(self, key)
        else:
            return key


class DictKey(object):
    def __init__(self, d, key):
        self.d = d
        self.key = key

    def __eq__(self, other):
        return self.d.eq_func(self.key, other.key)

    def __hash__(self):
        return self.d.hash_func(self.key)


class OrderedDictEntry(ExtRegistryEntry):
    _about_ = OrderedDict

    def compute_result_annotation(self, eq_func=None, hash_func=None):
        assert eq_func is None or eq_func.is_constant()
        assert hash_func is None or hash_func.is_constant()
        return SomeOrderedDict(getbookkeeper(), eq_func, hash_func)

    def specialize_call(self, hop):
        return hop.r_result.rtyper_new(hop)


class SomeOrderedDict(model.SomeObject):
    def __init__(self, bookkeeper, eq_func, hash_func):
        self.bookkeeper = bookkeeper

        self.eq_func = eq_func
        self.hash_func = hash_func

        self.key_type = model.s_ImpossibleValue
        self.value_type = model.s_ImpossibleValue

        self.read_locations = set()

    def __eq__(self, other):
        if not isinstance(other, SomeOrderedDict):
            return NotImplemented
        return (self.eq_func == other.eq_func and
            self.hash_func == other.hash_func and
            self.key_type == other.key_type and
            self.value_type == other.value_type
        )

    def rtyper_makerepr(self, rtyper):
        key_repr = rtyper.makerepr(self.key_type)
        value_repr = rtyper.makerepr(self.value_type)
        return OrderedDictRepr(rtyper, key_repr, value_repr)

    def generalize_key(self, s_key):
        new_key_type = model.unionof(self.key_type, s_key)
        if model.isdegenerated(new_key_type):
            self.bookkeeper.ondegenerated(self, new_key_type)
        if new_key_type != self.key_type:
            self.key_type = new_key_type
            for position_key in self.read_locations:
                self.bookkeeper.annotator.reflowfromposition(position_key)

    def generalize_value(self, s_value):
        new_value_type = model.unionof(self.value_type, s_value)
        if model.isdegenerated(new_value_type):
            self.bookkeeper.ondegenerated(self, new_value_type)
        if new_value_type != self.value_type:
            self.value_type = new_value_type
            for position_key in self.read_locations:
                self.bookkeeper.annotator.reflowfromposition(position_key)

    def read_value(self):
        position_key = self.bookkeeper.position_key
        self.read_locations.add(position_key)
        return self.value_type


class __extend__(pairtype(SomeOrderedDict, SomeOrderedDict)):
    def union((d1, d2)):
        assert d1.eq_func.const is d2.eq_func.const
        assert d1.hash_func.const is d2.hash_func.const
        s_new = SomeOrderedDict(d1.bookkeeper, d1.eq_func, d1.hash_func)
        s_new.key_type = d1.key_type = model.unionof(d1.key_type, d2.key_type)
        s_new.value_type = d1.value_type = model.unionof(d1.value_type, d2.value_type)
        return s_new


class __extend__(pairtype(SomeOrderedDict, model.SomeObject)):
    def setitem((self, key), s_value):
        self.generalize_key(key)
        self.generalize_value(s_value)

    def getitem((self, key)):
        self.generalize_key(key)
        return self.read_value()


class OrderedDictRepr(Repr):
    def __init__(self, rtyper, key_repr, value_repr):
        self.rtyper = rtyper
        self.key_repr = key_repr
        self.value_repr = value_repr

        self.lowleveltype = self.create_lowlevel_type()

    def create_lowlevel_type(self):
        entry_methods = {
            "valid": LLOrderedDict.ll_valid_from_flag,
            "everused": LLOrderedDict.ll_everused_from_flag,
        }
        DICTENTRY = lltype.Struct("ORDEREDDICTENTRY",
            ("key", self.key_repr.lowleveltype),
            ("value", self.value_repr.lowleveltype),
            ("next", lltype.Signed),
            ("everused", lltype.Bool),
            ("valid", lltype.Bool),
        )

        ll_keyeq = self.key_repr.get_ll_eq_function()
        if ll_keyeq is not None:
            ll_keyeq = lltype.staticAdtMethod(ll_keyeq)
        dict_methods = {
            "hashkey": lltype.staticAdtMethod(self.key_repr.get_ll_hash_function()),
            "keyeq": ll_keyeq,
        }
        DICT = lltype.GcStruct("ORDEREDDICT",
            ("num_items", lltype.Signed),
            ("resize_counter", lltype.Signed),
            ("first_entry", lltype.Signed),
            ("last_entry", lltype.Signed),
            ("entries", lltype.Ptr(lltype.GcArray(DICTENTRY, adtmeths=entry_methods))),
            adtmeths=dict_methods
        )
        return lltype.Ptr(DICT)


    def rtyper_new(self, hop):
        hop.exception_cannot_occur()
        c_TP = hop.inputconst(lltype.Void, self.lowleveltype.TO)
        return hop.gendirectcall(LLOrderedDict.ll_newdict, c_TP)


class __extend__(pairtype(OrderedDictRepr, Repr)):
    def rtype_setitem((self, r_key), hop):
        v_dict, v_key, v_value = hop.inputargs(
            self, self.key_repr, self.value_repr
        )
        hop.gendirectcall(LLOrderedDict.ll_setitem, v_dict, v_key, v_value)

    def rtype_getitem((self, r_key), hop):
        v_dict, v_key = hop.inputargs(self, self.key_repr)
        hop.exception_is_here()
        return hop.gendirectcall(LLOrderedDict.ll_getitem, v_dict, v_key)


class LLOrderedDict(object):
    INIT_SIZE = 8
    HIGHEST_BIT = intmask(1 << (LONG_BIT - 1))
    MASK = intmask(HIGHEST_BIT - 1)
    PERTURB_SHIFT = 5

    @staticmethod
    def ll_valid_from_flag(entries, i):
        return entries[i].valid

    @staticmethod
    def ll_everused_from_flag(entries, i):
        return entries[i].everused

    @staticmethod
    def ll_newdict(DICT):
        d = lltype.malloc(DICT)
        d.entries = lltype.malloc(DICT.entries.TO, LLOrderedDict.INIT_SIZE, zero=True)
        d.num_items = 0
        d.first_entry = -1
        d.last_entry = -1
        d.resize_counter = LLOrderedDict.INIT_SIZE * 2
        return d

    @staticmethod
    def ll_lookup(d, key, hash):
        entries = d.entries
        ENTRIES = lltype.typeOf(entries).TO
        mask = len(entries) - 1
        i = hash & mask
        if entries.valid(i):
            checkingkey = entries[i].key
            if checkingkey == key:
                return i
            if d.keyeq is not None and entries.hash(i) == hash:
                found = d.keyeq(checkingkey, key)
                if d.paranoia:
                    if (entries != d.entries or
                        not entries.valid(i) or entries[i] != checkingkey):
                        return LLOrderedDict.ll_lookup(d, key, hash)
                if found:
                    return i
            freeslot = -1
        elif entries.everused(i):
            freeslot = i
        else:
            return i | LLOrderedDict.HIGHEST_BIT

        perturb = r_uint(hash)
        while True:
            i = r_uint(i)
            i = (i << 2) + i + perturb + 1
            i = intmask(i) & mask
            if not entries.everused(i):
                if freeslot == -1:
                    freeslot = i
                return freeslot | LLOrderedDict.HIGHEST_BIT
            elif entries.valid(i):
                checkingkey = entries[i].key
                if checkingkey == key:
                    return i
                if d.keyeq is not None and entries.hash(i) == hash:
                    found = d.keyeq(checkingkey, key)
                    if d.paranoia:
                        if (entries != d.entries or
                            not entries.valid(i) or entries[i].key != checkingkey):
                            return LLOrderedDict.ll_lookup(d, key, hash)
                    if found:
                        return i
            elif freeslot == -1:
                freeslot = i
            perturb >>= LLOrderedDict.PERTURB_SHIFT

    @staticmethod
    def ll_setitem(d, key, value):
        hash = d.hashkey(key)
        i = LLOrderedDict.ll_lookup(d, key, hash)
        LLOrderedDict.ll_setitem_lookup_done(d, key, value, hash, i)

    @staticmethod
    def ll_setitem_lookup_done(d, key, value, hash, i):
        valid = (i & LLOrderedDict.HIGHEST_BIT) == 0
        i &= LLOrderedDict.MASK
        everused = d.entries.everused(i)
        ENTRY = lltype.typeOf(d.entries).TO.OF
        entry = d.entries[i]
        entry.value = value
        if valid:
            return
        entry.key = key
        if hasattr(ENTRY, "valid"):
            entry.valid = True
        d.num_items += 1
        if not everused:
            if hasattr(ENTRY, "everused"):
                entry.everused = True
            if d.first_entry == -1:
                d.first_entry = i
            else:
                d.entries[d.last_entry].next = i
            d.last_entry = i
            d.resize_counter -= 3
            if d.resize_counter <= 0:
                raise NotImplementedError("shrink")

    @staticmethod
    def ll_getitem(d, key):
        i = LLOrderedDict.ll_lookup(d, key, d.hashkey(key))
        if not i & LLOrderedDict.HIGHEST_BIT:
            return d.entries[i].value
        else:
            raise KeyError
