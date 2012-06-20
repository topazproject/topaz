from pypy.rlib import jit

from rupypy.module import ClassDef
from rupypy.objects.moduleobject import W_ModuleObject
from rupypy.objects.objectobject import W_Object


class W_ClassObject(W_ModuleObject):
    classdef = ClassDef("Class", W_ModuleObject.classdef)

    def __init__(self, space, name, superclass, is_singleton=False):
        W_ModuleObject.__init__(self, space, name, superclass)
        self.is_singleton = is_singleton

    def getsingletonclass(self, space):
        if self.klass is None:
            self.klass = space.newclass(
                self.name, space.getclassfor(W_ClassObject), is_singleton=True
            )
        return self.klass

    def find_method(self, space, method):
        res = W_ModuleObject.find_method(self, space, method)
        if res is None and self.superclass is not None:
            res = self.superclass.find_method(space, method)
        return res

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr(self.name)
    def ancestors(self):
        ary = W_ModuleObject.ancestors(self)
        if self.superclass is not None:
            ary += self.superclass.ancestors()
        return ary

    @classdef.method("new")
    def method_new(self, space, args_w):
        w_obj = space.send(self, space.newsymbol("allocate"), args_w)
        space.send(w_obj, space.newsymbol("initialize"), args_w)
        return w_obj

    @classdef.method("allocate")
    def method_allocate(self, space, args_w):
        return W_Object(space, self)
