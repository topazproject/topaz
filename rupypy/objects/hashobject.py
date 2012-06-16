from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_BaseObject
from rupypy.utils.ordereddict import OrderedDict


class W_HashObject(W_BaseObject):
    classdef = ClassDef("Hash", W_BaseObject.classdef)

    def __init__(self, space):
        self.contents = OrderedDict(space.eq_w, space.hash_w)

    @classdef.method("[]")
    def method_subscript(self, w_key):
        return self.contents[w_key]

    @classdef.method("[]=")
    def method_subscript_assign(self, w_key, w_value):
        self.contents[w_key] = w_value
        return w_value
