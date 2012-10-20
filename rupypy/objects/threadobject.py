import copy

from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object

from rupypy.celldict import CellDict


class W_ThreadObject(W_Object):
    classdef = ClassDef("Thread", W_Object.classdef)

    def __init__(self, space, args_w, block):
        W_Object.__init__(self, space)
        self.args_w = args_w
        self.block = block
        self.local_storage = CellDict()

    def __deepcopy__(self, memo):
        obj = super(W_ThreadObject, self).__deepcopy__(memo)
        obj.local_storage = copy.deepcopy(self.local_storage, memo)
        return obj

    @classdef.method("[]", key="str")
    def method_subscript(self, space, key):
        return self.local_storage.get(key) or space.w_nil

    @classdef.method("[]=", key="str")
    def method_subscript_assign(self, space, key, w_value):
        self.local_storage.set(key, w_value)
        return w_value

    @classdef.method("run")
    def method_run(self, space):
        raise space.error(space.w_NotImplementedError, "no threading yet")

    @classdef.singleton_method("current")
    def method_current(self, space):
        return space.w_main_thread

    @classdef.singleton_method("fork")
    @classdef.singleton_method("start")
    def method_start(self, space, args_w, block):
        w_obj = W_ThreadObject(space, args_w, block)
        # Must not call initialize
        space.send(w_obj, space.newsymbol("run"))
        return w_obj

    @classdef.singleton_method("new")
    def method_start(self, space, args_w, block):
        w_obj = W_ThreadObject(space, args_w, block)
        space.send(w_obj, space.newsymbol("initialize"), args_w)
        space.send(w_obj, space.newsymbol("run"))
        return w_obj
