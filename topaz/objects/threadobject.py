import copy
import weakref

from rpython.rlib import jit
from rpython.rlib.rshrinklist import AbstractShrinkList

from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object


class WRefShrinkList(AbstractShrinkList):
    def must_keep(self, wref):
        return wref() is not None


class W_ThreadObject(W_Object):
    _attrs_ = ["space"]
    classdef = ClassDef("Thread", W_Object.classdef)

    def __init__(self, space):
        W_Object.__init__(self, space)
        self.space = space

    def local_storage(self):
        return storage.get_or_create_local_storage(self.space)

    def __deepcopy__(self, memo):
        obj = super(W_ThreadObject, self).__deepcopy__(memo)
        local_storage_copy = copy.deepcopy(self.local_storage(), memo)
        storage.get_or_create_local_storage(self.space, local_storage_copy)
        return obj

    @classdef.singleton_method("current")
    def method_current(self, space):
        return space.w_main_thread

    @classdef.method("[]", key="str")
    def method_subscript(self, space, key):
        return self.local_storage().get(key, space.w_nil)

    @classdef.method("[]=", key="str")
    def method_subscript_assign(self, space, key, w_value):
        self.local_storage()[key] = w_value
        return w_value

    @classdef.method("recursion_guard")
    def method_recursion_guard(self, space, w_identifier, w_obj, block):
        """
        Calls the block with true if recursion is detected, false otherwise.
        It is up to the block to decide what to do in either case.
        """
        ec = space.getexecutioncontext()
        identifier = space.symbol_w(w_identifier)
        with ec.recursion_guard(identifier, w_obj) as in_recursion:
            if not in_recursion:
                space.invoke_block(block, [])
            return space.newbool(in_recursion)

    @classdef.method("in_recursion_guard?")
    def method_in_recursion_guardp(self, space, w_identifier):
        ec = space.getexecutioncontext()
        identifier = space.symbol_w(w_identifier)
        if identifier in ec.recursive_calls:
            return space.w_true
        return space.w_false


class Local():
    """Thread-local data"""

    @jit.dont_look_inside
    def __init__(self):
        self.dicts = {}  # mapping ExecutionContexts to storage dicts

    @jit.dont_look_inside
    def get_or_create_local_storage(self, space, initdata=None):
        ec = space.getexecutioncontext()
        if ec not in self.dicts or initdata is not None:
            self.dicts[ec] = initdata or {}
            self._register_in_ec(space, ec)
        return self.dicts[ec]

    def _register_in_ec(self, space, ec):
        if not space.config.translation.rweakref:
            return    # without weakrefs, works but 'dicts' is never cleared
        if ec._thread_local_objs is None:
            ec._thread_local_objs = WRefShrinkList()
        ec._thread_local_objs.append(weakref.ref(self))


storage = Local()
