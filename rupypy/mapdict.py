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
