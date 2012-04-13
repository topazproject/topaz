from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_BaseObject


class W_ArrayObject(W_BaseObject):
    classdef = ClassDef("Array", W_BaseObject.classdef)

    def __init__(self, items_w):
        self.items_w = items_w

    @classdef.method("to_s")
    def method_to_s(self, space):
        chars = []
        for w_item in self.items_w:
            w_s = space.send(w_item, space.newsymbol("to_s"))
            chars.extend(space.liststr_w(w_s))
        return space.newstr_fromchars(chars)

    @classdef.method("[]", idx=int)
    def method_subscript(self, space, idx):
        return self.items_w[idx]

    # classdef.app_method("to_s", """
    # def to_s()
    #     result = ""
    #     self.each do |o|
    #         result << o.to_s
    #     end
    #     return result
    # """)