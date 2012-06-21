from pypy.rlib import jit
from pypy.rlib.objectmodel import compute_unique_id

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

    def getclass(self, space):
        return space.getclassobject(self.classdef)

    def getnonsingletonclass(self, space):
        return self.getclass(space)

    def attach_method(self, space, name, func):
        w_cls = space.getsingletonclass(self)
        w_cls.define_method(space, name, func)

    def is_true(self, space):
        return True

    def object_id(self):
        return compute_unique_id(self)

    @classdef.method("__id__")
    def method___id__(self, space):
        return space.newint(self.object_id())

    @classdef.method("method_missing")
    def method_method_missing(self, space, w_name):
        name = space.symbol_w(w_name)
        class_name = space.str_w(space.send(self.getclass(space), space.newsymbol("name")))
        space.raise_(space.find_const(space.getclassfor(W_Object), "NoMethodError"),
            "undefined method `%s` for %s" % (name, class_name)
        )


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
    classdef = ClassDef("Object", W_BaseObject.classdef)

    def __init__(self, space, klass = None):
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

    def getnonsingletonclass(self, space):
        w_cls = self.getclass(space)
        if w_cls.is_singleton:
            return w_cls.superclass

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

    @classdef.method("initialize")
    def method_initialize(self):
        return self

    @classdef.method("object_id")
    def method_object_id(self, space):
        return W_BaseObject.method___id__(self, space)

    @classdef.method("singleton_class")
    def method_singleton_class(self, space):
        return space.getsingletonclass(self)

    @classdef.method("extend")
    def method_extend(self, space, w_mod):
        self.getsingletonclass(space).method_include(space, w_mod)

# Optimization for some classes defined in RPython with a classdef
# Avoids initializing a map and storage for objects without custom ivars
# Keeps singleton class in a local field and otherwise uses the BaseObject implementation
class W_BuiltinObject(W_Object):
    def __init__(self, space):
        self.map = None
        self.storage = None
        self.klass = None

    def ensure_map(self, space):
        if self.map is None:
            W_Object.__init__(self, space, space.getclassobject(self.classdef))

    def getclass(self, space):
        if self.klass is not None:
            return self.klass
        else:
            return W_BaseObject.getclass(self, space)

    def getsingletonclass(self, space):
        if self.klass is None:
            self.ensure_map(space)
            self.klass = W_Object.getsingletonclass(self, space)
        return self.klass

    def getnonsingletonclass(self, space):
        return W_BaseObject.getclass(self, space)

    def find_instance_var(self, space, name):
        self.ensure_map(space)
        idx = jit.promote(self.map).find_attr(space, name)
        if idx == -1:
            return space.w_nil
        return self.storage[idx]

    def set_instance_var(self, space, name, w_value):
        self.ensure_map(space)
        idx = jit.promote(self.map).find_set_attr(space, name)
        if idx == -1:
            idx = self.map.add_attr(space, self, name)
        self.storage[idx] = w_value
