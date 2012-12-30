import copy

from pypy.rlib import jit


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

    @jit.elidable
    def transition_add_flag(self, node, name, pos):
        return self.add_transitions.setdefault((node, name), FlagNode(node, name, pos))


class BaseNode(object):
    _attrs_ = ()

    def __deepcopy__(self, memo):
        memo[id(self)] = result = object.__new__(self.__class__)
        return result

    def add_attr(self, space, w_obj, name):
        attr_node = space.fromcache(MapTransitionCache).transition_add_attr(w_obj.map, name, len(w_obj.storage))
        w_obj.map = attr_node
        w_obj.storage.append(None)
        return attr_node.pos

    def add_flag(self, space, w_obj, name):
        flag_node = space.fromcache(MapTransitionCache).transition_add_flag(w_obj.map, name, len(w_obj.storage))
        w_obj.map = flag_node
        w_obj.storage.append(space.w_true)


class ClassNode(BaseNode):
    _immutable_fields_ = ["klass"]

    def __init__(self, klass):
        self.klass = klass

    def __deepcopy__(self, memo):
        obj = super(ClassNode, self).__deepcopy__(memo)
        obj.klass = copy.deepcopy(self.klass, memo)
        return obj

    def get_class(self):
        return self.klass

    def find_attr(self, space, name):
        return -1

    def find_set_attr(self, space, name):
        return -1

    def find_flag(self, space, name):
        return -1

    def change_class(self, space, w_cls):
        return space.fromcache(MapTransitionCache).get_class_node(w_cls)

    def add_attr(self, space, w_obj, name):
        w_obj.storage = []
        return BaseNode.add_attr(self, space, w_obj, name)

    def add_flag(self, space, w_obj, name):
        w_obj.storage = []
        BaseNode.add_flag(self, space, w_obj, name)

    def copy_attrs(self, space, w_obj, w_target):
        pass

    def copy_flags(self, space, w_obj, w_target):
        pass


class StorageNode(BaseNode):
    _immutable_fields_ = ["prev", "name", "pos"]

    def __init__(self, prev, name, pos):
        self.prev = prev
        self.name = name
        self.pos = pos

    @jit.elidable
    def get_class(self):
        return self.prev.get_class()


class AttributeNode(StorageNode):
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

    @jit.elidable
    def find_flag(self, space, name):
        return self.prev.find_flag(space, name)

    def change_class(self, space, w_cls):
        prev = self.prev.change_class(space, w_cls)
        return space.fromcache(MapTransitionCache).transition_add_attr(prev, self.name, self.pos)

    def copy_attrs(self, space, w_obj, w_target):
        self.prev.copy_attrs(space, w_obj, w_target)
        w_target.set_instance_var(space, self.name, w_obj.storage[self.pos])

    def copy_flags(self, space, w_obj, w_target):
        self.prev.copy_flags(space, w_obj, w_target)


class FlagNode(StorageNode):
    @jit.elidable
    def find_attr(self, space, name):
        return self.prev.find_attr(space, name)

    @jit.elidable
    def find_set_attr(self, space, name):
        return self.prev.find_set_attr(space, name)

    @jit.elidable
    def find_flag(self, space, name):
        if name == self.name:
            return self.pos
        else:
            return self.prev.find_flag(space, name)

    def change_class(self, space, w_cls):
        prev = self.prev.change_class(space, w_cls)
        return space.fromcache(MapTransitionCache).transition_add_flag(prev, self.name, self.pos)

    def copy_attrs(self, space, w_obj, w_target):
        self.prev.copy_attrs(space, w_obj, w_target)

    def copy_flags(self, space, w_obj, w_target):
        self.prev.copy_flags(space, w_obj, w_target)
        if w_obj.storage[self.pos] is space.w_true:
            # Only copy flags that are still set
            w_target.set_flag(space, self.name)
