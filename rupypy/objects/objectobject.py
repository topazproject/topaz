from pypy.rlib import jit
from pypy.rlib.objectmodel import compute_unique_id

from rupypy.mapdict import MapTransitionCache
from rupypy.module import ClassDef


class ObjectMetaclass(type):
    def __new__(cls, name, bases, attrs):
        new_cls = super(ObjectMetaclass, cls).__new__(cls, name, bases, attrs)
        if "classdef" in attrs:
            attrs["classdef"].cls = new_cls
        return new_cls


class W_BaseObject(object):
    __metaclass__ = ObjectMetaclass
    _attrs_ = ()

    classdef = ClassDef("BasicObject")

    @classmethod
    def setup_class(cls, space, w_cls):
        pass

    def getclass(self, space):
        return space.getclassobject(self.classdef)

    def attach_method(self, space, name, func):
        w_cls = space.getsingletonclass(self)
        w_cls.define_method(space, name, func)

    def is_true(self, space):
        return True

    @classdef.method("initialize")
    def method_initialize(self):
        return self

    @classdef.method("__id__")
    def method___id__(self, space):
        return space.newint(compute_unique_id(self))

    @classdef.method("method_missing")
    def method_method_missing(self, space, w_name):
        name = space.symbol_w(w_name)
        class_name = space.str_w(space.send(self.getclass(space), space.newsymbol("name")))
        space.raise_(space.find_const(space.getclassfor(W_Object), "NoMethodError"),
            "undefined method `%s` for %s" % (name, class_name)
        )

    @classdef.method("==")
    @classdef.method("equal?")
    def method_eq(self, space, w_other):
        return space.newbool(self is w_other)

    @classdef.method("!")
    def method_not(self, space):
        equal = space.newsymbol("equal?")
        return space.newbool(
            space.is_true(space.send(self, equal, [space.w_false])) or
            space.is_true(space.send(self, equal, [space.w_nil]))
        )

    @classdef.method("!=")
    def method_ne(self, space, w_other):
        return space.newbool(
            not space.is_true(space.send(self, space.newsymbol("=="), [w_other]))
        )

    @classdef.method("__send__", method="str")
    def method_send(self, space, method, args_w, block):
        return space.send(self, space.newsymbol(method), args_w[1:], block)

class W_RootObject(W_BaseObject):
    classdef = ClassDef("Object", W_BaseObject.classdef)

    @classdef.method("object_id")
    def method_object_id(self, space):
        return space.send(self, space.newsymbol("__id__"))

    @classdef.method("singleton_class")
    def method_singleton_class(self, space):
        return space.getsingletonclass(self)

    @classdef.method("extend")
    def method_extend(self, space, w_mod):
        self.getsingletonclass(space).method_include(space, w_mod)

    @classdef.method("to_s")
    def method_to_s(self, space):
        return space.newstr_fromstr("#<%s:0x%x>" % (
            space.str_w(space.send(space.getclass(self), space.newsymbol("name"))),
            space.int_w(space.send(self, space.newsymbol("__id__")))
        ))

    @classdef.method("==")
    def method_equal(self, space, w_other):
        return space.newbool(self is w_other)


    @classdef.method("send")
    def method_send(self, space, args_w, block):
        return space.send(self, space.newsymbol("__send__"), args_w, block)

class W_Object(W_RootObject):
    def __init__(self, space, klass=None):
        if klass is None:
            klass = space.getclassfor(self.__class__)
        self.map = space.fromcache(MapTransitionCache).get_class_node(klass)
        self.storage = []

    def getclass(self, space):
        return jit.promote(self.map).get_class()

    def getsingletonclass(self, space):
        w_cls = jit.promote(self.map).get_class()
        if w_cls.is_singleton:
            return w_cls
        w_cls = space.newclass(w_cls.name, w_cls, is_singleton=True)
        self.map = self.map.change_class(space, w_cls)
        return w_cls

    def find_instance_var(self, space, name):
        idx = jit.promote(self.map).find_attr(space, name)
        if idx == -1:
            return space.w_nil
        return self.storage[idx]

    def set_instance_var(self, space, name, w_value):
        idx = jit.promote(self.map).find_set_attr(space, name)
        if idx == -1:
            idx = self.map.add_attr(space, self, name)
        self.storage[idx] = w_value
