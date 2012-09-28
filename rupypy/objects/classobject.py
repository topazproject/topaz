from rupypy.module import ClassDef
from rupypy.objects.moduleobject import W_ModuleObject
from rupypy.objects.objectobject import W_Object


class W_ClassObject(W_ModuleObject):
    classdef = ClassDef("Class", W_ModuleObject.classdef)

    def __init__(self, space, name, superclass, is_singleton=False):
        W_ModuleObject.__init__(self, space, name, superclass)
        self.is_singleton = is_singleton

        if self.superclass is not None:
            self.superclass.inherited(space, self)
            # During bootstrap, we cannot create singleton classes, yet
            if not self.is_singleton and not space.bootstrap:
                self.getsingletonclass(space)

    def getsingletonclass(self, space):
        if self.klass is None:
            if self.superclass is None:
                singleton_superclass = space.w_class
            else:
                singleton_superclass = self.superclass.getsingletonclass(space)
            self.klass = space.newclass(
                "#<Class:%s>" % self.name, singleton_superclass, is_singleton=True
            )
        return self.klass

    def find_method(self, space, name):
        method = W_ModuleObject.find_method(self, space, name)
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

    @classdef.method("new")
    def method_new(self, space, args_w, block):
        w_obj = space.send(self, space.newsymbol("allocate"), args_w, block)
        space.send(w_obj, space.newsymbol("initialize"), args_w, block)
        return w_obj

    @classdef.method("allocate")
    def method_allocate(self, space, args_w):
        return W_Object(space, self)
