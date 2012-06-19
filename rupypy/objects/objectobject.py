from pypy.rlib import jit
from pypy.rlib.objectmodel import compute_unique_id

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

    def attach_method(self, space, name, func):
        w_cls = space.getsingletonclass(self)
        w_cls.define_method(space, name, func)

    def is_true(self, space):
        return True

    @classdef.method("initialize")
    def method_initialize(self):
        return self

    @classdef.method("object_id")
    def method_object_id(self, space):
        return space.newint(compute_unique_id(self))

    @classdef.method("singleton_class")
    def method_singleton_class(self, space):
        return space.getsingletonclass(self)

    @classdef.method("extend")
    def method_extend(self, space, w_mod):
        self.getsingletonclass(space).method_include(space, w_mod)

class MapTransitionCache(object):
    def __init__(self, space):
        # Mappings of classes -> their terminator nodes.
        self.class_nodes = {}
        # Mapping of (current_node, name) -> new node
        self.add_transitions = {}

    @jit.elidable
    def get_class_node(self, klass):
        return self.class_nodes.setdefault(klass, ClassNode(klass))

    @jit.elidable
    def transition_add_attr(self, node, name, pos):
        return self.add_transitions.setdefault((node, name), AttributeNode(node, name, pos))


class BaseNode(object):
    _attrs_ = ()

    def add_attr(self, space, w_obj, name):
        attr_node = space.fromcache(MapTransitionCache).transition_add_attr(w_obj.map, name, len(w_obj.storage))
        w_obj.map = attr_node
        w_obj.storage.append(None)
        return attr_node.pos


class ClassNode(BaseNode):
    _immutable_fields_ = ["klass"]

    def __init__(self, klass):
        self.klass = klass

    def get_class(self):
        return self.klass

    def find_attr(self, space, name):
        return -1

    def find_set_attr(self, space, name):
        return -1

    def change_class(self, space, w_cls):
        return space.fromcache(MapTransitionCache).get_class_node(w_cls)


class AttributeNode(BaseNode):
    _immutable_fields_ = ["prev", "name", "pos"]

    def __init__(self, prev, name, pos):
        self.prev = prev
        self.name = name
        self.pos = pos

    @jit.elidable
    def get_class(self):
        return self.prev.get_class()

    @jit.elidable
    def find_attr(self, space, name):
        if name == self.name:
            return self.pos
        else:
            return self.prev.find_attr(space, name)

    @jit.elidable
    def find_set_attr(self, space, name):
        if name == self.name:
            return self.pos
        else:
            return self.prev.find_set_attr(space, name)

    def change_class(self, space, w_cls):
        prev = self.prev.change_class(space, w_cls)
        return space.fromcache(MapTransitionCache).transition_add_attr(prev, self.name, self.pos)


class W_Object(W_BaseObject):
    def __init__(self, space, klass):
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
