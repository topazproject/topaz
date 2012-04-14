from rupypy.module import ClassDef
from rupypy.modules.kernel import Kernel


class ObjectMetaclass(type):
    def __new__(cls, name, bases, attrs):
        new_cls = super(ObjectMetaclass, cls).__new__(cls, name, bases, attrs)
        if "classdef" in attrs:
            attrs["classdef"].cls = new_cls
        return new_cls

class W_BaseObject(object):
    __metaclass__ = ObjectMetaclass
    _attrs_ = ()

    classdef = ClassDef("Object")
    classdef.include_module(Kernel)

    def getclass(self, space):
        return space.getclassobject(self.classdef)

    def add_method(self, space, name, function):
        # Not legal, I don't think
        raise NotImplementedError

    def is_true(self, space):
        return True

    @classdef.method("initialize")
    def method_initialize(self, space):
        return self


class W_Object(W_BaseObject):
    def __init__(self, klass=None):
        self.klass = klass

    def getclass(self, space):
        if self.klass is None:
            return W_BaseObject.getclass(self, space)
        return self.klass

    def add_method(self, space, name, function):
        if self.klass is None:
            w_current_class = self.getclass(space)
            self.klass = space.newclass(w_current_class.name, w_current_class)
        self.klass.add_method(space, name, function)
