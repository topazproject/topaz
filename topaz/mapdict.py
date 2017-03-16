from rpython.rlib import jit, longlong2float
from rpython.rlib.objectmodel import specialize
from rpython.rlib.rarithmetic import intmask
from rpython.rlib.unroll import unrolling_iterable
from rpython.rtyper.lltypesystem import rffi, lltype


NUM_DIGITS = 4
NUM_DIGITS_POW2 = 1 << NUM_DIGITS


class MapTransitionCache(object):
    def __init__(self, space):
        # {w_cls: ClassNode}
        self.class_nodes = {}
        # {(prev_node, node_cls, name): BaseNode}
        self.transitions = {}

    @jit.elidable
    def get_class_node(self, w_cls):
        return self.class_nodes.setdefault(w_cls, ClassNode(w_cls))

    @jit.elidable
    def get_transition(self, prev, node_cls, name):
        return self.transitions.setdefault(
            (prev, node_cls, name), node_cls(prev, name))


class BaseNode(object):
    _attrs_ = ["size_estimate"]
    _immutable_fields_ = ["size_estimate"]

    @jit.elidable
    def find(self, node_cls, name=None):
        node = self
        while node is not None:
            if node.matches(node_cls, name):
                return node
            node = node.getprev()

    def matches(self, node_cls, name):
        return isinstance(self, node_cls)

    def add(self, space, node_cls, name, w_obj):
        new_node = space.fromcache(MapTransitionCache).get_transition(
            self, node_cls, name)
        new_node.update_storage_size(w_obj, self)
        return new_node


class ClassNode(BaseNode):
    _immutable_fields_ = ["w_cls"]

    uses_object_storage = uses_unboxed_storage = False

    def __init__(self, w_cls):
        self.w_cls = w_cls
        self.size_estimate = SizeEstimate(0, 0)

    def getclass(self):
        return self.w_cls

    def change_class(self, space, new_cls):
        return space.fromcache(MapTransitionCache).get_class_node(new_cls)

    def copy_attrs(self, space, w_obj, w_target):
        pass

    def getprev(self):
        return None


class StorageNode(BaseNode):
    _immutable_fields_ = ["prev", "name", "pos"]

    def __init__(self, prev, name):
        self.prev = prev
        self.name = name
        self.pos = self.compute_position()

    def length(self):
        return self.pos + 1

    def getprev(self):
        return self.prev

    def change_class(self, space, w_cls):
        new_prev = self.prev.change_class(space, w_cls)
        return space.fromcache(MapTransitionCache).get_transition(
            new_prev, self.__class__, self.name)

    def matches(self, node_cls, name):
        return BaseNode.matches(self, node_cls, name) and name == self.name

    def update_storage_size(self, w_obj, prev_node):
        if not jit.we_are_jitted():
            prev_node.size_estimate.update_from(self.size_estimate)


class AttributeNode(StorageNode):
    @staticmethod
    def select_type(space, w_value):
        for cls in ATTRIBUTE_CLASSES:
            if cls.correct_type(space, w_value):
                return cls

    def copy_attrs(self, space, w_obj, w_target):
        self.prev.copy_attrs(space, w_obj, w_target)
        w_target.set_instance_var(space, self.name, self.read(space, w_obj))

    def write(self, space, w_obj, w_value):
        if not self.correct_type(space, w_value):
            w_obj.map = w_obj.map.remove_attr(space, self, w_obj)
            w_obj.map = node = w_obj.map.add(
                space, AttributeNode.select_type(space, w_value),
                self.name, w_obj)
            node.write(space, w_obj, w_value)
        else:
            self._store(space, w_obj, w_value)

    def remove_attr(self, space, node, w_obj):
        if node is self:
            return self.prev
        w_cur_val = self.read(space, w_obj)
        new_prev = self.prev.remove_attr(space, node, w_obj)
        node = new_prev.add(
            space, AttributeNode.select_type(space, w_cur_val), self.name,
            w_obj)
        node.write(space, w_obj, w_cur_val)
        return node


class UnboxedAttributeNode(AttributeNode):
    uses_object_storage = False
    uses_unboxed_storage = True

    def __init__(self, prev, name):
        AttributeNode.__init__(self, prev, name)
        self.size_estimate = SizeEstimate(
            prev.size_estimate._object_size_estimate,
            self.length() * NUM_DIGITS_POW2
        )

    def compute_position(self):
        return compute_position(self, "uses_unboxed_storage")

    def update_storage_size(self, w_obj, prev_node):
        AttributeNode.update_storage_size(self, w_obj, prev_node)
        update_storage(self, w_obj, "unboxed", 0.0)


class IntAttributeNode(UnboxedAttributeNode):
    @staticmethod
    def correct_type(space, w_value):
        return space.is_kind_of(w_value, space.w_fixnum)

    def _store(self, space, w_obj, w_value):
        w_obj.unboxed_storage[self.pos] = longlong2float.longlong2float(
            rffi.cast(lltype.SignedLongLong, space.int_w(w_value)))

    def read(self, space, w_obj):
        return space.newint(intmask(longlong2float.float2longlong(
            w_obj.unboxed_storage[self.pos])))


class FloatAttributeNode(UnboxedAttributeNode):
    @staticmethod
    def correct_type(space, w_value):
        return space.is_kind_of(w_value, space.w_float)

    def _store(self, space, w_obj, w_value):
        w_obj.unboxed_storage[self.pos] = space.float_w(w_value)

    def read(self, space, w_obj):
        return space.newfloat(w_obj.unboxed_storage[self.pos])


class ObjectAttributeNode(AttributeNode):
    uses_object_storage = True
    uses_unboxed_storage = False

    def __init__(self, prev, name):
        AttributeNode.__init__(self, prev, name)
        self.size_estimate = SizeEstimate(
            self.length() * NUM_DIGITS_POW2,
            prev.size_estimate._unboxed_size_estimate,
        )

    @staticmethod
    def correct_type(space, w_value):
        return True

    def compute_position(self):
        return compute_position(self, "uses_object_storage")

    def update_storage_size(self, w_obj, prev_node):
        AttributeNode.update_storage_size(self, w_obj, prev_node)
        update_storage(self, w_obj, "object", None)

    def _store(self, space, w_obj, w_value):
        w_obj.object_storage[self.pos] = w_value

    def read(self, space, w_obj):
        return w_obj.object_storage[self.pos]


class FlagNode(StorageNode):
    uses_object_storage = True
    uses_unboxed_storage = False

    def __init__(self, prev, name):
        StorageNode.__init__(self, prev, name)
        self.size_estimate = SizeEstimate(
            self.length() * NUM_DIGITS_POW2,
            prev.size_estimate._unboxed_size_estimate,
        )

    def compute_position(self):
        return compute_position(self, "uses_object_storage")

    def update_storage_size(self, w_obj, prev_node):
        StorageNode.update_storage_size(self, w_obj, prev_node)
        update_storage(self, w_obj, "object", None)

    def copy_attrs(self, space, w_obj, w_target):
        self.prev.copy_attrs(space, w_obj, w_target)

    def write(self, space, w_obj, w_value):
        w_obj.object_storage[self.pos] = w_value

    def read(self, space, w_obj):
        return w_obj.object_storage[self.pos]


ATTRIBUTE_CLASSES = unrolling_iterable([
    IntAttributeNode,
    FloatAttributeNode,
    ObjectAttributeNode,
])


@specialize.arg(2)
@jit.unroll_safe
def update_storage(node, w_obj, storage_name, empty_value):
    storage = getattr(w_obj, storage_name + "_storage")
    if storage is None or node.length() >= len(storage):
        new_storage = [empty_value] * getattr(
            node.size_estimate, storage_name + "_size_estimate")()
        if storage is not None:
            for i, value in enumerate(storage):
                new_storage[i] = value
        setattr(w_obj, storage_name + "_storage", new_storage)


@specialize.arg(1)
def compute_position(node, predicate):
    node = node.getprev()
    n = 0
    while node is not None:
        if getattr(node, predicate):
            n += 1
        node = node.getprev()
    return n


class SizeEstimate(object):
    def __init__(self, object_size_estimate, unboxed_size_estimate):
        self._object_size_estimate = object_size_estimate
        self._unboxed_size_estimate = unboxed_size_estimate

    @jit.elidable
    def object_size_estimate(self):
        return self._object_size_estimate >> NUM_DIGITS

    @jit.elidable
    def unboxed_size_estimate(self):
        return self._unboxed_size_estimate >> NUM_DIGITS

    def update_from(self, other):
        self._object_size_estimate = (self._object_size_estimate +
                                      other.object_size_estimate() -
                                      self.object_size_estimate())
        self._unboxed_size_estimate = (self._unboxed_size_estimate +
                                       other.unboxed_size_estimate() -
                                       self.unboxed_size_estimate())
