import operator
import copy
from collections import OrderedDict as PyOrderedDict

from rpython.annotator import model
from rpython.annotator.bookkeeper import getbookkeeper
from rpython.rlib.objectmodel import hlinvoke
from rpython.rlib.rarithmetic import r_uint, intmask, LONG_BIT
from rpython.rtyper.extregistry import ExtRegistryEntry
from rpython.rtyper.lltypesystem import lltype
from rpython.rtyper.rmodel import Repr, IteratorRepr, externalvsinternal
from rpython.tool.pairtype import pairtype


MARKER = object()


class OrderedDict(object):
    def __init__(self, eq_func=None, hash_func=None):
        self.contents = PyOrderedDict()
        self.eq_func = eq_func or operator.eq
        self.hash_func = hash_func or hash

    def __getitem__(self, key):
        return self.contents[self._key(key)]

    def __setitem__(self, key, value):
        self.contents[self._key(key)] = value

    def __delitem__(self, key):
        del self.contents[self._key(key)]

    def __contains__(self, key):
        return self._key(key) in self.contents

    def __len__(self):
        return len(self.contents)

    def _key(self, key):
        return DictKey(self, key)

    def keys(self):
        return [k.key for k in self.contents.keys()]

    def values(self):
        return self.contents.values()

    def iteritems(self):
        for k, v in self.contents.iteritems():
            yield k.key, v

    def get(self, key, default):
        return self.contents.get(self._key(key), default)

    def pop(self, key, default=MARKER):
        if default is MARKER:
            return self.contents.pop(self._key(key))
        else:
            return self.contents.pop(self._key(key), default)

    def popitem(self):
        if not self:
            raise KeyError
        k, v = self.contents.popitem()
        return k.key, v

    def update(self, d):
        self.contents.update(d.contents)

    def clear(self):
        self.contents.clear()

    def copy(self):
        d = OrderedDict(self.eq_func, self.hash_func)
        for k, v in self.iteritems():
            d[k] = v
        return d


class DictKey(object):
    def __init__(self, d, key):
        self.d = d
        self.key = key
        self.hash = None

    def __eq__(self, other):
        return self.d.eq_func(self.key, other.key)

    def __hash__(self):
        if self.hash is None:
            self.hash = self.d.hash_func(self.key)
        return self.hash


class OrderedDictEntry(ExtRegistryEntry):
    _about_ = OrderedDict

    def compute_result_annotation(self, s_eq_func=None, s_hash_func=None):
        assert s_eq_func is None or s_eq_func.is_constant()
        assert s_hash_func is None or s_hash_func.is_constant()

        if s_eq_func is None and s_hash_func is None:
            dictdef = getbookkeeper().getdictdef()
        else:
            dictdef = getbookkeeper().getdictdef(is_r_dict=True)
            dictdef.dictkey.update_rdict_annotations(s_eq_func, s_hash_func)

        return SomeOrderedDict(getbookkeeper(), dictdef,)

    def specialize_call(self, hop):
        return hop.r_result.rtyper_new(hop)


class SomeOrderedDict(model.SomeObject):
    def __init__(self, bookkeeper, dictdef):
        self.bookkeeper = bookkeeper
        self.dictdef = dictdef

    def __eq__(self, other):
        if not isinstance(other, SomeOrderedDict):
            return NotImplemented
        return self.dictdef.same_as(other.dictdef)

    def rtyper_makerepr(self, rtyper):
        key_repr = rtyper.getrepr(self.dictdef.dictkey.s_value)
        value_repr = rtyper.getrepr(self.dictdef.dictvalue.s_value)
        if self.dictdef.dictkey.custom_eq_hash:
            eq_func_repr = rtyper.getrepr(self.dictdef.dictkey.s_rdict_eqfn)
            hash_func_repr = rtyper.getrepr(self.dictdef.dictkey.s_rdict_hashfn)
        else:
            eq_func_repr = None
            hash_func_repr = None
        return OrderedDictRepr(rtyper, key_repr, value_repr, eq_func_repr, hash_func_repr)

    def rtyper_makekey(self):
        return (type(self), self.dictdef.dictkey, self.dictdef.dictvalue)

    def method_keys(self):
        return self.bookkeeper.newlist(self.dictdef.read_key())

    def method_values(self):
        return self.bookkeeper.newlist(self.dictdef.read_value())

    def method_iteritems(self):
        return SomeOrderedDictIterator(self)

    def method_get(self, s_key, s_default):
        self.dictdef.generalize_key(s_key)
        self.dictdef.generalize_value(s_default)
        return self.dictdef.read_value()

    def method_pop(self, s_key, s_default=None):
        self.dictdef.generalize_key(s_key)
        if s_default is not None:
            self.dictdef.generalize_value(s_default)
        return self.dictdef.read_value()

    def method_popitem(self):
        s_key = self.dictdef.read_key()
        s_value = self.dictdef.read_value()
        if (isinstance(s_key, model.SomeImpossibleValue) or
            isinstance(s_value, model.SomeImpossibleValue)):
            return model.s_ImpossibleValue
        return model.SomeTuple((s_key, s_value))

    def method_update(self, s_dict):
        assert isinstance(s_dict, SomeOrderedDict)
        self.dictdef.union(s_dict.dictdef)

    def method_copy(self):
        return SomeOrderedDict(self.bookkeeper, self.dictdef)

    def method_clear(self):
        pass


class SomeOrderedDictIterator(model.SomeObject):
    def __init__(self, d):
        super(SomeOrderedDictIterator, self).__init__()
        self.d = d

    def rtyper_makerepr(self, rtyper):
        return OrderedDictIteratorRepr(rtyper.getrepr(self.d))

    def rtyper_makekey(self):
        return (type(self), self.d)

    def iter(self):
        return self

    def next(self):
        s_key = self.d.dictdef.read_key()
        s_value = self.d.dictdef.read_value()
        if (isinstance(s_key, model.SomeImpossibleValue) or
            isinstance(s_value, model.SomeImpossibleValue)):
            return model.s_ImpossibleValue
        return model.SomeTuple((s_key, s_value))
    method_next = next


class __extend__(pairtype(SomeOrderedDict, SomeOrderedDict)):
    def union((d1, d2)):
        return SomeOrderedDict(getbookkeeper(), d1.dictdef.union(d2.dictdef))


class __extend__(pairtype(SomeOrderedDict, model.SomeObject)):
    def setitem((self, key), s_value):
        self.dictdef.generalize_key(key)
        self.dictdef.generalize_value(s_value)

    def getitem((self, key)):
        self.dictdef.generalize_key(key)
        return self.dictdef.read_value()

    def delitem((self, key)):
        self.dictdef.generalize_key(key)

    def contains((self, key)):
        self.generalize_key(key)
        return model.s_Bool


class OrderedDictRepr(Repr):
    def __init__(self, rtyper, key_repr, value_repr, eq_func_repr, hash_func_repr):
        self.rtyper = rtyper
        self.eq_func_repr = eq_func_repr
        self.hash_func_repr = hash_func_repr
        self.external_key_repr, self.key_repr = self.pickrepr(key_repr)
        self.external_value_repr, self.value_repr = self.pickrepr(value_repr)

        self.lowleveltype = self.create_lowlevel_type()

    def pickrepr(self, item_repr):
        if self.eq_func_repr and self.hash_func_repr:
            return item_repr, item_repr
        else:
            return externalvsinternal(self.rtyper, item_repr)

    def _must_clear(self, ll_tp):
        return isinstance(ll_tp, lltype.Ptr) and ll_tp._needsgc()

    def create_lowlevel_type(self):
        entry_methods = {
            "valid": LLOrderedDict.ll_valid_from_flag,
            "everused": LLOrderedDict.ll_everused_from_flag,
            "mark_deleted": LLOrderedDict.ll_mark_deleted_in_flag,
            "must_clear_key": self._must_clear(self.key_repr.lowleveltype),
            "must_clear_value": self._must_clear(self.value_repr.lowleveltype),
        }
        fields = [
            ("key", self.key_repr.lowleveltype),
            ("value", self.value_repr.lowleveltype),
            ("next", lltype.Signed),
            ("prev", lltype.Signed),
            ("everused", lltype.Bool),
            ("valid", lltype.Bool),
        ]
        fast_hash_func = None
        if not self.hash_func_repr:
            fast_hash_func = self.key_repr.get_ll_hash_function()
        if fast_hash_func is None:
            fields.append(("hash", lltype.Signed))
            entry_methods["hash"] = LLOrderedDict.ll_hash_from_cache
        else:
            entry_methods["hash"] = LLOrderedDict.ll_hash_recompute
            entry_methods["fast_hash_func"] = fast_hash_func
        DICTENTRY = lltype.Struct("ORDEREDDICTENTRY", *fields)

        fields = [
            ("num_items", lltype.Signed),
            ("resize_counter", lltype.Signed),
            ("first_entry", lltype.Signed),
            ("last_entry", lltype.Signed),
            ("entries", lltype.Ptr(lltype.GcArray(DICTENTRY, adtmeths=entry_methods))),
        ]
        dict_methods = {}
        if self.eq_func_repr and self.hash_func_repr:
            dict_methods["paranoia"] = True
            dict_methods["hashkey"] = LLOrderedDict.ll_hashkey_custom
            dict_methods["keyeq"] = LLOrderedDict.ll_keyeq_custom

            dict_methods["r_hashkey"] = self.hash_func_repr
            dict_methods["r_keyeq"] = self.eq_func_repr

            fields.append(("hashkey_func", self.hash_func_repr.lowleveltype))
            fields.append(("keyeq_func", self.eq_func_repr.lowleveltype))
        else:
            dict_methods["paranoia"] = False
            dict_methods["hashkey"] = lltype.staticAdtMethod(self.key_repr.get_ll_hash_function())
            ll_keyeq = self.key_repr.get_ll_eq_function()
            if ll_keyeq is not None:
                ll_keyeq = lltype.staticAdtMethod(ll_keyeq)
            dict_methods["keyeq"] = ll_keyeq

        DICT = lltype.GcStruct("ORDEREDDICT", *fields, adtmeths=dict_methods)
        return lltype.Ptr(DICT)

    def recast_value(self, hop, v):
        return hop.llops.convertvar(v, self.value_repr, self.external_value_repr)

    def rtyper_new(self, hop):
        hop.exception_cannot_occur()
        c_TP = hop.inputconst(lltype.Void, self.lowleveltype.TO)
        v_res = hop.gendirectcall(LLOrderedDict.ll_newdict, c_TP)
        if self.eq_func_repr and self.hash_func_repr:
            v_eq = hop.inputarg(self.eq_func_repr, arg=0)
            v_hash = hop.inputarg(self.hash_func_repr, arg=1)
            cname = hop.inputconst(lltype.Void, "keyeq_func")
            hop.genop("setfield", [v_res, cname, v_eq])
            cname = hop.inputconst(lltype.Void, "hashkey_func")
            hop.genop("setfield", [v_res, cname, v_hash])
        return v_res

    def rtype_len(self, hop):
        [v_dict] = hop.inputargs(self)
        return hop.gendirectcall(LLOrderedDict.ll_len, v_dict)

    def rtype_method_keys(self, hop):
        [v_dict] = hop.inputargs(self)
        r_list = hop.r_result
        c_LIST = hop.inputconst(lltype.Void, r_list.lowleveltype.TO)
        return hop.gendirectcall(LLOrderedDict.ll_keys, c_LIST, v_dict)

    def rtype_method_values(self, hop):
        [v_dict] = hop.inputargs(self)
        r_list = hop.r_result
        c_LIST = hop.inputconst(lltype.Void, r_list.lowleveltype.TO)
        return hop.gendirectcall(LLOrderedDict.ll_values, c_LIST, v_dict)

    def rtype_method_iteritems(self, hop):
        return OrderedDictIteratorRepr(self).newiter(hop)

    def rtype_method_get(self, hop):
        v_dict, v_key, v_default = hop.inputargs(self, self.key_repr, self.value_repr)
        return hop.gendirectcall(LLOrderedDict.ll_get, v_dict, v_key, v_default)

    def rtype_method_pop(self, hop):
        if hop.nb_args == 2:
            v_args = hop.inputargs(self, self.key_repr)
            target = LLOrderedDict.ll_pop
        elif hop.nb_args == 3:
            v_args = hop.inputargs(self, self.key_repr, self.value_repr)
            target = LLOrderedDict.ll_pop_default
        hop.exception_is_here()
        v_res = hop.gendirectcall(target, *v_args)
        return self.recast_value(hop, v_res)

    def rtype_method_popitem(self, hop):
        hop.exception_is_here()
        [v_dict] = hop.inputargs(self)
        c_TP = hop.inputconst(lltype.Void, hop.r_result.lowleveltype)
        return hop.gendirectcall(LLOrderedDict.ll_popitem, c_TP, v_dict)

    def rtype_method_update(self, hop):
        [v_dict, v_other] = hop.inputargs(self, self)
        return hop.gendirectcall(LLOrderedDict.ll_update, v_dict, v_other)

    def rtype_method_clear(self, hop):
        [v_dict] = hop.inputargs(self)
        return hop.gendirectcall(LLOrderedDict.ll_clear, v_dict)

    def rtype_method_copy(self, hop):
        [v_dict] = hop.inputargs(self)
        return hop.gendirectcall(LLOrderedDict.ll_copy, v_dict)


class OrderedDictIteratorRepr(IteratorRepr):
    def __init__(self, r_dict):
        super(OrderedDictIteratorRepr, self).__init__()
        self.r_dict = r_dict

        self.lowleveltype = self.create_lowlevel_type()

    def create_lowlevel_type(self):
        return lltype.Ptr(lltype.GcStruct("ORDEREDDICTITER",
            ("d", self.r_dict.lowleveltype),
            ("index", lltype.Signed),
        ))

    def newiter(self, hop):
        [v_dict] = hop.inputargs(self.r_dict)
        c_TP = hop.inputconst(lltype.Void, self.lowleveltype.TO)
        return hop.gendirectcall(LLOrderedDict.ll_newdictiter, c_TP, v_dict)

    def rtype_next(self, hop):
        [v_iter] = hop.inputargs(self)
        c_TP = hop.inputconst(lltype.Void, hop.r_result.lowleveltype)
        hop.exception_is_here()
        return hop.gendirectcall(LLOrderedDict.ll_dictiternext, c_TP, v_iter)


class __extend__(pairtype(OrderedDictRepr, Repr)):
    def rtype_setitem((self, r_key), hop):
        v_dict, v_key, v_value = hop.inputargs(
            self, self.key_repr, self.value_repr
        )
        hop.gendirectcall(LLOrderedDict.ll_setitem, v_dict, v_key, v_value)

    def rtype_getitem((self, r_key), hop):
        v_dict, v_key = hop.inputargs(self, self.key_repr)
        hop.exception_is_here()
        v_res = hop.gendirectcall(LLOrderedDict.ll_getitem, v_dict, v_key)
        return self.recast_value(hop, v_res)

    def rtype_delitem((self, r_key), hop):
        v_dict, v_key = hop.inputargs(self, self.key_repr)
        hop.exception_is_here()
        hop.gendirectcall(LLOrderedDict.ll_delitem, v_dict, v_key)

    def rtype_contains((self, r_key), hop):
        v_dict, v_key = hop.inputargs(self, self.key_repr)
        return hop.gendirectcall(LLOrderedDict.ll_contains, v_dict, v_key)


class __extend__(pairtype(OrderedDictRepr, OrderedDictRepr)):
    def convert_from_to((d1, d2), v, llops):
        if (d1.key_repr is not d2.key_repr or
            d1.value_repr is not d2.value_repr or
            d1.eq_func_repr is not d2.eq_func_repr or
            d1.hash_func_repr is not d2.hash_func_repr):
            return NotImplemented
        return v


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
    def ll_mark_deleted_in_flag(entries, i):
        entries[i].valid = False

    @staticmethod
    def ll_hashkey_custom(d, key):
        DICT = lltype.typeOf(d).TO
        return hlinvoke(DICT.r_hashkey, d.hashkey_func, key)

    @staticmethod
    def ll_keyeq_custom(d, key1, key2):
        DICT = lltype.typeOf(d).TO
        return hlinvoke(DICT.r_keyeq, d.keyeq_func, key1, key2)

    @staticmethod
    def ll_hash_recompute(entries, i):
        ENTRIES = lltype.typeOf(entries).TO
        return ENTRIES.fast_hash_func(entries[i].key)

    @staticmethod
    def ll_hash_from_cache(entries, i):
        return entries[i].hash

    @staticmethod
    def recast(P, v):
        if isinstance(P, lltype.Ptr):
            return lltype.cast_pointer(P, v)
        else:
            return v

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
    def ll_len(d):
        return d.num_items

    @staticmethod
    def ll_lookup(d, key, hash):
        entries = d.entries
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
                        not entries.valid(i) or entries[i].key != checkingkey):
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
        if hasattr(ENTRY, "hash"):
            entry.hash = hash
        if hasattr(ENTRY, "valid"):
            entry.valid = True
        d.num_items += 1
        if d.first_entry == -1:
            d.first_entry = i
        else:
            d.entries[d.last_entry].next = i
        entry.prev = d.last_entry
        d.last_entry = i
        entry.next = -1
        if not everused:
            if hasattr(ENTRY, "everused"):
                entry.everused = True
            d.resize_counter -= 3
            if d.resize_counter <= 0:
                LLOrderedDict.ll_resize(d)

    @staticmethod
    def ll_getitem(d, key):
        i = LLOrderedDict.ll_lookup(d, key, d.hashkey(key))
        if not i & LLOrderedDict.HIGHEST_BIT:
            return d.entries[i].value
        else:
            raise KeyError

    @staticmethod
    def ll_delitem(d, key):
        i = LLOrderedDict.ll_lookup(d, key, d.hashkey(key))
        if i & LLOrderedDict.HIGHEST_BIT:
            raise KeyError
        LLOrderedDict._ll_del(d, i)

    @staticmethod
    def _ll_del(d, i):
        d.entries.mark_deleted(i)
        d.num_items -= 1
        entry = d.entries[i]
        if entry.prev == -1:
            d.first_entry = entry.next
        else:
            d.entries[entry.prev].next = entry.next
        if entry.next == -1:
            d.last_entry = entry.prev
        else:
            d.entries[entry.next].prev = entry.prev

        ENTRIES = lltype.typeOf(d.entries).TO
        ENTRY = ENTRIES.OF
        if ENTRIES.must_clear_key:
            entry.key = lltype.nullptr(ENTRY.key.TO)
        if ENTRIES.must_clear_value:
            entry.value = lltype.nullptr(ENTRY.value.TO)

    @staticmethod
    def ll_contains(d, key):
        i = LLOrderedDict.ll_lookup(d, key, d.hashkey(key))
        return not bool(i & LLOrderedDict.HIGHEST_BIT)

    @staticmethod
    def ll_resize(d):
        old_entries = d.entries
        if d.num_items > 50000:
            new_estimate = d.num_items * 2
        else:
            new_estimate = d.num_items * 4

        new_size = LLOrderedDict.INIT_SIZE
        while new_size <= new_estimate:
            new_size *= 2

        d.entries = lltype.malloc(lltype.typeOf(old_entries).TO, new_size, zero=True)
        d.num_items = 0
        d.resize_counter = new_size * 2

        i = d.first_entry
        d.first_entry = -1
        d.last_entry = -1

        while i != -1:
            hash = old_entries.hash(i)
            entry = old_entries[i]
            LLOrderedDict.ll_insert_clean(d, entry.key, entry.value, hash)
            i = entry.next

    @staticmethod
    def ll_insert_clean(d, key, value, hash):
        i = LLOrderedDict.ll_lookup_clean(d, hash)
        ENTRY = lltype.typeOf(d.entries).TO.OF
        entry = d.entries[i]
        entry.value = value
        entry.key = key
        if hasattr(ENTRY, "hash"):
            entry.hash = hash
        if hasattr(ENTRY, "valid"):
            entry.valid = True
        if hasattr(ENTRY, "everused"):
            entry.everused = True
        d.num_items += 1
        if d.first_entry == -1:
            d.first_entry = i
        else:
            d.entries[d.last_entry].next = i
        entry.prev = d.last_entry
        d.last_entry = i
        entry.next = -1
        d.resize_counter -= 3

    @staticmethod
    def ll_lookup_clean(d, hash):
        entries = d.entries
        mask = len(entries) - 1
        i = hash & mask
        perturb = r_uint(hash)
        while entries.everused(i):
            i = r_uint(i)
            i = (i << 2) + i + perturb + 1
            i = intmask(i) & mask
            perturb >>= LLOrderedDict.PERTURB_SHIFT
        return i

    @staticmethod
    def ll_keys(LIST, d):
        res = LIST.ll_newlist(d.num_items)
        ELEM = lltype.typeOf(res.ll_items()).TO.OF
        i = 0
        idx = d.first_entry
        while idx != -1:
            res.ll_items()[i] = LLOrderedDict.recast(ELEM, d.entries[idx].key)
            idx = d.entries[idx].next
            i += 1
        return res

    @staticmethod
    def ll_values(LIST, d):
        res = LIST.ll_newlist(d.num_items)
        ELEM = lltype.typeOf(res.ll_items()).TO.OF
        i = 0
        idx = d.first_entry
        while idx != -1:
            res.ll_items()[i] = LLOrderedDict.recast(ELEM, d.entries[idx].value)
            idx = d.entries[idx].next
            i += 1
        return res

    @staticmethod
    def ll_get(d, key, default):
        i = LLOrderedDict.ll_lookup(d, key, d.hashkey(key))
        if not i & LLOrderedDict.HIGHEST_BIT:
            return d.entries[i].value
        else:
            return default

    @staticmethod
    def ll_pop(d, key):
        i = LLOrderedDict.ll_lookup(d, key, d.hashkey(key))
        if not i & LLOrderedDict.HIGHEST_BIT:
            value = d.entries[i].value
            LLOrderedDict._ll_del(d, i)
            return value
        else:
            raise KeyError

    @staticmethod
    def ll_pop_default(d, key, default):
        try:
            return LLOrderedDict.ll_pop(d, key)
        except KeyError:
            return default

    @staticmethod
    def ll_popitem(RESTYPE, d):
        if not d.num_items:
            raise KeyError
        entry = d.entries[d.first_entry]

        r = lltype.malloc(RESTYPE.TO)
        r.item0 = LLOrderedDict.recast(RESTYPE.TO.item0, entry.key)
        r.item1 = LLOrderedDict.recast(RESTYPE.TO.item1, entry.value)

        LLOrderedDict._ll_del(d, d.first_entry)

        return r

    @staticmethod
    def ll_update(d, other):
        idx = other.first_entry
        while idx != -1:
            entry = other.entries[idx]
            i = LLOrderedDict.ll_lookup(d, entry.key, other.entries.hash(idx))
            LLOrderedDict.ll_setitem_lookup_done(d, entry.key, entry.value, other.entries.hash(idx), i)
            idx = entry.next

    @staticmethod
    def ll_clear(d):
        if d.num_items == 0:
            return
        d.entries = lltype.malloc(lltype.typeOf(d.entries).TO, LLOrderedDict.INIT_SIZE, zero=True)
        d.num_items = 0
        d.first_entry = -1
        d.last_entry = -1
        d.resize_counter = LLOrderedDict.INIT_SIZE * 2

    @staticmethod
    def ll_copy(d):
        DICT = lltype.typeOf(d).TO
        new_d = lltype.malloc(DICT)
        new_d.entries = lltype.malloc(DICT.entries.TO, len(d.entries), zero=True)
        new_d.num_items = d.num_items
        new_d.resize_counter = d.resize_counter
        new_d.first_entry = d.first_entry
        new_d.last_entry = d.last_entry
        if hasattr(DICT, "hashkey_func"):
            new_d.hashkey_func = d.hashkey_func
        if hasattr(DICT, "keyeq_func"):
            new_d.keyeq_func = d.keyeq_func
        for i in xrange(len(d.entries)):
            entry = d.entries[i]
            new_entry = new_d.entries[i]
            new_entry.key = entry.key
            new_entry.value = entry.value
            new_entry.next = entry.next
            new_entry.prev = entry.prev
            new_entry.everused = entry.everused
            new_entry.valid = entry.valid
            if hasattr(DICT.entries.TO.OF, "hash"):
                new_entry.hash = entry.hash
        return new_d

    @staticmethod
    def ll_newdictiter(ITER, d):
        it = lltype.malloc(ITER)
        it.d = d
        it.index = d.first_entry
        return it

    @staticmethod
    def ll_dictiternext(RESTYPE, it):
        if it.index == -1:
            raise StopIteration
        r = lltype.malloc(RESTYPE.TO)
        entry = it.d.entries[it.index]
        r.item0 = LLOrderedDict.recast(RESTYPE.TO.item0, entry.key)
        r.item1 = LLOrderedDict.recast(RESTYPE.TO.item1, entry.value)
        it.index = entry.next
        return r
