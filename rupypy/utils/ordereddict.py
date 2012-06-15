from collections import OrderedDict as PyOrderedDict

from pypy.annotation import model
from pypy.annotation.bookkeeper import getbookkeeper
from pypy.rpython.extregistry import ExtRegistryEntry
from pypy.rpython.lltypesystem import lltype
from pypy.rpython.rmodel import Repr
from pypy.tool.pairtype import pairtype


class OrderedDict(object):
    def __init__(self):
        self.contents = PyOrderedDict()

    def __getitem__(self, key):
        return self.contents[key]

    def __setitem__(self, key, value):
        self.contents[self._key(key)] = value

    def _key(self, key):
        return key


class OrderedDictEntry(ExtRegistryEntry):
    _about_ = OrderedDict

    def compute_result_annotation(self):
        return SomeOrderedDict(getbookkeeper())

    def specialize_call(self, hop):
        return hop.r_result.rtyper_new(hop)


class SomeOrderedDict(model.SomeObject):
    def __init__(self, bookkeeper):
        self.bookkeeper = bookkeeper

        self.key_type = model.s_ImpossibleValue
        self.value_type = model.s_ImpossibleValue

        self.read_locations = set()

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
        return self.key_type


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
        DICTENTRY = lltype.Struct("ORDEREDDICTENTRY",
            ("key", self.key_repr.lowleveltype),
            ("value", self.value_repr.lowleveltype),
            ("next", lltype.Signed),
        )

        DICT = lltype.GcStruct("ORDEREDDICT",
            ("num_items", lltype.Signed),
            ("resize_counter", lltype.Signed),
            ("first_entry", lltype.Signed),
            ("entries", lltype.Ptr(lltype.GcArray(DICTENTRY)))
        )
        return lltype.Ptr(DICT)

    def rtyper_new(self, hop):
        hop.exception_cannot_occur()
        c_TP = hop.inputconst(lltype.Void, self.lowleveltype.TO)
        return hop.gendirectcall(LLOrderedDict.ll_newdict, c_TP)


class LLOrderedDict(object):
    INIT_SIZE = 8

    @classmethod
    def ll_newdict(cls, DICT):
        d = lltype.malloc(DICT)
        d.entries = lltype.malloc(DICT.entries.TO, cls.INIT_SIZE, zero=True)
        d.num_items = 0
        d.first_entry = -1
        d.resize_counter = cls.INIT_SIZE * 2
        return d
