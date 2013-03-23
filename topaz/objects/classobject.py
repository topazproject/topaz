import copy

from topaz.module import ClassDef
from topaz.objects.moduleobject import W_ModuleObject
from topaz.objects.objectobject import W_Object


class W_ClassObject(W_ModuleObject):
    _immutable_fields_ = ["superclass"]

    classdef = ClassDef("Class", W_ModuleObject.classdef, filepath=__file__)

    def __init__(self, space, name, superclass, is_singleton=False):
        W_ModuleObject.__init__(self, space, name)
        self.superclass = superclass
        self.is_singleton = is_singleton

        if self.superclass is not None:
            self.superclass.inherited(space, self)
            # During bootstrap, we cannot create singleton classes, yet
            if not self.is_singleton and not space.bootstrap:
                self.getsingletonclass(space)

    def __deepcopy__(self, memo):
        obj = super(W_ClassObject, self).__deepcopy__(memo)
        obj.is_singleton = self.is_singleton
        obj.superclass = copy.deepcopy(self.superclass, memo)
        return obj

    def getsingletonclass(self, space):
        if self.klass is None:
            if self.superclass is None:
                singleton_superclass = space.w_class
            else:
                singleton_superclass = self.superclass.getsingletonclass(space)
            if self.name is None:
                name = None
            else:
                name = "#<Class:%s>" % self.name
            self.klass = space.newclass(
                name, singleton_superclass, is_singleton=True
            )
        return self.klass

    def find_const(self, space, name):
        w_res = W_ModuleObject.find_included_const(self, space, name)
        if w_res is None and self.superclass is not None:
            w_res = self.superclass.find_const(space, name)
        return w_res

    def find_method(self, space, name):
        method = W_ModuleObject.find_method(self, space, name)
        if method is None and self.superclass is not None:
            method = self.superclass.find_method(space, name)
        return method

    def find_method_super(self, space, name):
        method = W_ModuleObject.find_method_super(self, space, name)
        if method is None and self.superclass is not None:
            method = self.superclass.find_method(space, name)
        return method

    def ancestors(self, include_singleton=True, include_self=True):
        assert include_self
        ary = W_ModuleObject.ancestors(self,
            include_singleton, not (self.is_singleton and not include_singleton)
        )
        if self.superclass is not None:
            ary += self.superclass.ancestors(include_singleton)
        return ary

    def inherited(self, space, w_mod):
        self.descendants.append(w_mod)
        if not space.bootstrap and space.respond_to(self, space.newsymbol("inherited")):
            space.send(self, space.newsymbol("inherited"), [w_mod])

    @classdef.singleton_method("allocate")
    def singleton_method_allocate(self, space, w_superclass=None):
        if w_superclass is not None:
            assert isinstance(w_superclass, W_ClassObject)
        else:
            w_superclass = space.w_object
        return space.newclass(None, w_superclass)

    @classdef.method("initialize")
    def method_initialize(self, space, args_w):
        pass

    @classdef.method("new")
    def method_new(self, space, args_w, block):
        w_obj = space.send(self, space.newsymbol("allocate"), args_w, block)
        space.send(w_obj, space.newsymbol("initialize"), args_w, block)
        return w_obj

    @classdef.method("allocate")
    def method_allocate(self, space, args_w):
        return W_Object(space, self)

    @classdef.method("superclass")
    def method_superclass(self, space):
        return self.superclass if self.superclass is not None else space.w_nil
