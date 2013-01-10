import copy

from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object


class W_ThreadObject(W_Object):
    classdef = ClassDef("Thread", W_Object.classdef, filepath=__file__)

    def __init__(self, space):
        W_Object.__init__(self, space)
        # TODO: This should be a map dict.
        self.local_storage = {}

    def __deepcopy__(self, memo):
        obj = super(W_ThreadObject, self).__deepcopy__(memo)
        obj.local_storage = copy.deepcopy(self.local_storage, memo)
        return obj

    @classdef.singleton_method("current")
    def method_current(self, space):
        return space.w_main_thread

    @classdef.method("[]", key="str")
    def method_subscript(self, space, key):
        return self.local_storage.get(key, space.w_nil)

    @classdef.method("[]=", key="str")
    def method_subscript_assign(self, space, key, w_value):
        self.local_storage[key] = w_value
        return w_value
