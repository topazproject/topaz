import copy

from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object


class W_ThreadObject(W_Object):
    classdef = ClassDef("Thread", W_Object.classdef)

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
