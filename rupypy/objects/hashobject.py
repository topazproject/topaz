from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object
from rupypy.utils.ordereddict import OrderedDict


class W_HashObject(W_Object):
    classdef = ClassDef("Hash", W_Object.classdef)

    def __init__(self, space):
        W_Object.__init__(self, space)
        self.contents = OrderedDict(space.eq_w, space.hash_w)

    @classdef.method("[]")
    def method_subscript(self, space, w_key):
        return self.contents.get(w_key, space.w_nil)

    @classdef.method("[]=")
    def method_subscript_assign(self, w_key, w_value):
        self.contents[w_key] = w_value
        return w_value

    @classdef.method("keys")
    def method_keys(self, space):
        return space.newarray(self.contents.keys())

    @classdef.method("each")
    def method_each(self, space, block):
        for k in self.contents.keys():
            space.invoke_block(block, [k, self.contents.get(k, space.w_nil)])
        return self
