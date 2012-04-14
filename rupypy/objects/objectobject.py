from pypy.rlib import jit

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

class ClassNode(BaseNode):
    _immutable_attrs_ = ["klass"]
    def __init__(self, klass):
        self.klass = klass

    def get_class(self):
        return self.klass

    def find_attr(self, space, w_obj, name):
        return None

    def set_attr(self, space, w_obj, name, w_value):
        attr_node = space.fromcache(MapTransitionCache).transition_add_attr(w_obj.map, name, len(w_obj.storage))
        attr_node.add_attr(space, w_obj, name, w_value)

    def change_class(self, space, w_obj, new_class_node):
        return new_class_node

class AttributeNode(BaseNode):
    _immutable_attrs_ = ["prev", "name", "pos"]
    def __init__(self, prev, name, pos):
        self.prev = prev
        self.name = name
        self.pos = pos

    def get_class(self):
        return self.prev.get_class()

    def find_attr(self, space, w_obj, name):
        if name == self.name:
            return w_obj.storage[self.pos]
        else:
            return self.prev.find_attr(space, w_obj, name)

    def set_attr(self, space, w_obj, name, w_value):
        if name == self.name:
            w_obj.storage[self.pos] = w_value
        else:
            self.prev.set_attr(space, w_obj, name, w_value)

    def add_attr(self, space, w_obj, name, w_value):
        assert name == self.name
        w_obj.map = self
        w_obj.storage.append(w_value)


class W_Object(W_BaseObject):
    def __init__(self, space, klass):
        self.map = space.fromcache(MapTransitionCache).get_class_node(klass)
        self.storage = []

    def getclass(self, space):
        return self.map.get_class()

    def add_method(self, space, name, function):
        klass = self.getclass(space)
        if not klass.is_singleton:
            new_klass = space.newclass(klass.name, klass)
            new_class_node = space.fromcache(MapTransitionCache).get_class_node(new_klass)
            self.map = self.map.change_class(space, self, new_class_node)
        self.getclass(space).add_method(space, name, function)

    def find_instance_var(self, space, name):
        return jit.promote(self.map).find_attr(space, self, name)

    def set_instance_var(self, space, name, w_value):
        self.map.set_attr(space, self, name, w_value)
