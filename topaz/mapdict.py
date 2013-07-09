from rpython.rlib import jit
from rpython.rlib.objectmodel import specialize


NOT_FOUND = -1
CLASS = 0
FLAG = 1
ATTR = 2
INT_ATTR = 3
FLOAT_ATTR = 4
OBJECT_ATTR = 5

ATTR_DOES_NOT_EXIST = -1
ATTR_WRONG_TYPE = -2

# note: we use "x * NUM_DIGITS_POW2" instead of "x << NUM_DIGITS" because we
# want to propagate knowledge that the result cannot be negative
NUM_DIGITS = 4
NUM_DIGITS_POW2 = 1 << NUM_DIGITS


class MapTransitionCache(object):
    def __init__(self, space):
        # {w_cls: class_node}
        self.class_nodes = {}
        # {(node, selector, name): new_node}
        self.transitions = {}

    @jit.elidable
    def get_class_node(self, w_cls):
        return self.class_nodes.setdefault(w_cls, ClassNode(w_cls))

    @jit.elidable
    def get_transition(self, node, selector, name, obj_pos, unboxed_pos):
        return self.transitions.setdefault((node, selector, name), AttributeNode(node, selector, name, obj_pos, unboxed_pos))


class BaseNode(object):
    _attrs_ = ["_object_size_estimate", "_unboxed_size_estimate"]

    def __init__(self):
        self._object_size_estimate = 0
        self._unboxed_size_estimate = 0

    def raw_size_estimate(self, selector):
        if selector == OBJECT_ATTR or selector == FLAG:
            return self._object_size_estimate
        elif selector == INT_ATTR or selector == FLOAT_ATTR:
            return self._unboxed_size_estimate
        else:
            raise SystemError

    @jit.elidable
    def size_estimate(self, selector):
        if selector == OBJECT_ATTR or selector == FLAG:
            return self._object_size_estimate >> NUM_DIGITS
        elif selector == INT_ATTR or selector == FLOAT_ATTR:
            return self._unboxed_size_estimate >> NUM_DIGITS
        else:
            raise SystemError

    def add(self, space, selector, name, w_obj):
        if selector == OBJECT_ATTR or selector == FLAG:
            pos = obj_pos = self.length(selector)
            unboxed_pos = -1
        elif selector == INT_ATTR or selector == FLOAT_ATTR:
            obj_pos = -1
            pos = unboxed_pos = self.length(selector)
        else:
            raise SystemError
        new_node = space.fromcache(MapTransitionCache).get_transition(self, selector, name, obj_pos, unboxed_pos)
        self.update_storage_size(new_node, w_obj)
        return new_node, pos

    @jit.unroll_safe
    def update_storage_size(self, new_node, w_obj):
        selector = new_node.selector
        if not jit.we_are_jitted():
            size_est = self.raw_size_estimate(selector) + new_node.size_estimate(selector) - self.size_estimate(selector)
            assert size_est >= (self.length(selector) * NUM_DIGITS_POW2)
            if selector == OBJECT_ATTR or selector == FLAG:
                self._object_size_estimate = size_est
            elif selector == INT_ATTR or selector == FLOAT_ATTR:
                self._unboxed_size_estimate = size_est
            else:
                raise SystemError
        if new_node.length(selector) >= self.length(selector):
            # note that node.size_estimate() is always at least node.length()
            new_size = new_node.size_estimate(selector)
            if selector == OBJECT_ATTR or selector == FLAG:
                if w_obj.object_storage:
                    new_size = max(new_size, len(w_obj.object_storage))
                new_storage = [None] * new_size
                if w_obj.object_storage:
                    for i, w_value in enumerate(w_obj.object_storage):
                        new_storage[i] = w_value
                w_obj.object_storage = new_storage
            elif selector == INT_ATTR or selector == FLOAT_ATTR:
                if w_obj.unboxed_storage:
                    new_size = max(new_size, len(w_obj.unboxed_storage))
                new_storage = [0.0] * new_size
                if w_obj.unboxed_storage:
                    for i, value in enumerate(w_obj.unboxed_storage):
                        new_storage[i] = value
                w_obj.unboxed_storage = new_storage
            else:
                raise SystemError


class ClassNode(BaseNode):
    _attrs_ = ["w_cls"]

    def __init__(self, w_cls):
        BaseNode.__init__(self)
        self.w_cls = w_cls

    @jit.elidable
    @specialize.arg(1)
    def read(self, selector, name=None):
        if selector == CLASS:
            return self.w_cls
        elif selector == FLAG:
            return ATTR_DOES_NOT_EXIST
        elif (selector == ATTR or selector == INT_ATTR or
            selector == FLOAT_ATTR or selector == OBJECT_ATTR):
            return ATTR_DOES_NOT_EXIST, NOT_FOUND
        else:
            raise NotImplementedError

    def replace(self, space, selector, w_value):
        if selector == CLASS:
            return space.fromcache(MapTransitionCache).get_class_node(w_value)
        else:
            raise NotImplementedError

    def length(self, selector):
        return 0

    def pos(self, selector):
        return -1

    def copy_attrs(self, space, w_obj, w_target):
        pass


class AttributeNode(BaseNode):
    def __init__(self, prev, selector, name, obj_pos, unboxed_pos):
        BaseNode.__init__(self)
        self.prev = prev
        self.selector = selector
        self.name = name
        self._obj_pos = obj_pos
        self._unboxed_pos = unboxed_pos
        if selector == OBJECT_ATTR or selector == FLAG:
            self._object_size_estimate = self.length(selector) * NUM_DIGITS_POW2
        elif selector == INT_ATTR or selector == FLOAT_ATTR:
            self._unboxed_size_estimate = self.length(selector) * NUM_DIGITS_POW2
        else:
            raise SystemError

    @jit.elidable
    @specialize.arg(1)
    def read(self, selector, name=None):
        if selector == CLASS:
            return self.prev.read(selector)
        elif selector == ATTR:
            if name == self.name:
                return self.pos(self.selector), self.selector
            else:
                return self.prev.read(selector, name)
        elif selector == FLAG:
            if selector == self.selector and self.name == name:
                return self.pos(selector)
            else:
                return self.prev.read(selector, name)
        elif (selector == OBJECT_ATTR or selector == INT_ATTR or
            selector == FLOAT_ATTR):
            if name == self.name:
                if selector == self.selector:
                    return self.pos(selector), selector
                else:
                    return ATTR_WRONG_TYPE, self.selector
            else:
                return self.prev.read(selector, name)
        else:
            raise NotImplementedError

    def replace(self, space, selector, w_cls):
        back = self.prev.replace(space, selector, w_cls)
        return space.fromcache(MapTransitionCache).get_transition(back, self.selector, self.name, self._obj_pos, self._unboxed_pos)

    def length(self, selector):
        if selector == self.selector:
            if selector == OBJECT_ATTR or selector == FLAG:
                return self._obj_pos + 1
            elif selector == INT_ATTR or selector == FLOAT_ATTR:
                return self._unboxed_pos + 1
            else:
                raise SystemError
        else:
            return self.prev.length(selector)

    def pos(self, selector):
        if selector == self.selector:
            if selector == OBJECT_ATTR or selector == FLAG:
                return self._obj_pos
            elif selector == INT_ATTR or selector == FLOAT_ATTR:
                return self._unboxed_pos
            else:
                raise SystemError
        else:
            return self.prev.pos(selector)

    def copy_attrs(self, space, w_obj, w_target):
        self.prev.copy_attrs(space, w_obj, w_target)
        if self.selector != FLAG:
            w_target.set_instance_var(space, self.name, w_obj.find_instance_var(space, self.name))
