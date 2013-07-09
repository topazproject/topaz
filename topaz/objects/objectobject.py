import copy

from rpython.rlib import jit, longlong2float
from rpython.rlib.objectmodel import compute_unique_id
from rpython.rlib.rarithmetic import intmask

from topaz import mapdict
from topaz.module import ClassDef
from topaz.scope import StaticScope


class ObjectMetaclass(type):
    def __new__(cls, name, bases, attrs):
        new_cls = super(ObjectMetaclass, cls).__new__(cls, name, bases, attrs)
        if "classdef" in attrs:
            attrs["classdef"].cls = new_cls
        return new_cls


class W_Root(object):
    _attrs_ = []
    __metaclass__ = ObjectMetaclass

    def __deepcopy__(self, memo):
        obj = object.__new__(self.__class__)
        memo[id(self)] = obj
        return obj


class W_BaseObject(W_Root):
    _attrs_ = []

    classdef = ClassDef("BasicObject")

    def getclass(self, space):
        return space.getclassobject(self.classdef)

    def is_kind_of(self, space, w_cls):
        return w_cls.is_ancestor_of(self.getclass(space))

    def attach_method(self, space, name, func):
        w_cls = space.getsingletonclass(self)
        w_cls.define_method(space, name, func)

    def is_true(self, space):
        return True

    def find_const(self, space, name):
        raise space.error(space.w_TypeError,
            "%s is not a class/module" % space.str_w(space.send(self, "inspect"))
        )
    find_included_const = find_local_const = find_const

    @classdef.method("initialize")
    def method_initialize(self):
        return self

    @classdef.method("__id__")
    def method___id__(self, space):
        return space.newint(compute_unique_id(self))

    @classdef.method("method_missing")
    def method_method_missing(self, space, w_name, args_w):
        name = space.symbol_w(w_name)
        class_name = space.str_w(space.send(self.getclass(space), "to_s"))
        raise space.error(space.w_NoMethodError,
            "undefined method `%s' for %s" % (name, class_name)
        )

    @classdef.method("==")
    @classdef.method("equal?")
    def method_eq(self, space, w_other):
        return space.newbool(self is w_other)

    @classdef.method("!")
    def method_not(self, space):
        return space.newbool(not space.is_true(self))

    @classdef.method("!=")
    def method_ne(self, space, w_other):
        return space.newbool(
            not space.is_true(space.send(self, "==", [w_other]))
        )

    @classdef.method("__send__", method="str")
    def method_send(self, space, method, args_w, block):
        return space.send(self, method, args_w, block)

    @classdef.method("instance_eval", string="str", filename="str")
    def method_instance_eval(self, space, string=None, filename=None, w_lineno=None, block=None):
        if string is not None:
            if filename is None:
                filename = "instance_eval"
            if w_lineno is not None:
                lineno = space.int_w(w_lineno)
            else:
                lineno = 1
            return space.execute(string, self, StaticScope(space.getclass(self), None), filename, lineno)
        else:
            return space.invoke_block(block.copy(space, w_self=self), [])

    @classdef.method("singleton_method_removed")
    def method_singleton_method_removed(self, space, w_name):
        return space.w_nil

    @classdef.method("singleton_method_added")
    def method_singleton_method_added(self, space, w_name):
        return space.w_nil

    @classdef.method("singleton_method_undefined")
    def method_singleton_method_undefined(self, space, w_name):
        return space.w_nil

    @classdef.method("instance_exec")
    def method_instance_exec(self, space, args_w, block):
        if block is None:
            raise space.error(space.w_LocalJumpError, "no block given")

        if space.is_kind_of(self, space.w_symbol) or space.is_kind_of(self, space.w_numeric):
            self_klass = None
        else:
            self_klass = space.getsingletonclass(self)

        return space.invoke_block(
            block.copy(
                space,
                w_self=self,
                lexical_scope=StaticScope(self_klass, block.lexical_scope)
            ),
            args_w
        )


class W_RootObject(W_BaseObject):
    _attrs_ = []

    classdef = ClassDef("Object", W_BaseObject.classdef)

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        space.w_top_self = W_Object(space, w_cls)


class W_Object(W_RootObject):
    _attrs_ = ["map", "object_storage", "unboxed_storage"]

    def __init__(self, space, klass=None):
        if klass is None:
            klass = space.getclassfor(self.__class__)
        self.map = space.fromcache(mapdict.MapTransitionCache).get_class_node(klass)
        self.object_storage = None
        self.unboxed_storage = None

    def __deepcopy__(self, memo):
        obj = super(W_Object, self).__deepcopy__(memo)
        obj.map = copy.deepcopy(self.map, memo)
        obj.object_storage = copy.deepcopy(self.object_storage, memo)
        obj.unboxed_storage = copy.deepcopy(self.unboxed_storage, memo)
        return obj

    def getclass(self, space):
        w_cls = jit.promote(self.map).read(mapdict.CLASS)
        return w_cls

    def getsingletonclass(self, space):
        w_cls = jit.promote(self.map).read(mapdict.CLASS)
        if w_cls.is_singleton:
            return w_cls
        w_cls = space.newclass(w_cls.name, w_cls, is_singleton=True, attached=self)
        self.map = self.map.replace(space, mapdict.CLASS, w_cls)
        return w_cls

    def copy_singletonclass(self, space, w_other):
        w_cls = jit.promote(self.map).read(mapdict.CLASS)
        assert not w_cls.is_singleton
        w_copy = space.newclass(w_cls.name, w_cls, is_singleton=True, attached=self)
        w_copy.methods_w.update(w_other.methods_w)
        w_copy.constants_w.update(w_other.constants_w)
        w_copy.included_modules = w_copy.included_modules + w_other.included_modules
        w_copy.mutated()

        self.map = self.map.replace(space, mapdict.CLASS, w_copy)
        return w_cls

    def find_instance_var(self, space, name):
        idx, tp = jit.promote(self.map).read(mapdict.ATTR, name)
        if idx == mapdict.ATTR_DOES_NOT_EXIST:
            return None
        if tp == mapdict.INT_ATTR:
            return space.newint(intmask(longlong2float.float2longlong(self.unboxed_storage[idx])))
        elif tp == mapdict.FLOAT_ATTR:
            return space.newfloat(self.unboxed_storage[idx])
        elif tp == mapdict.OBJECT_ATTR:
            return self.object_storage[idx]
        else:
            raise SystemError

    def set_instance_var(self, space, name, w_value):
        if space.is_kind_of(w_value, space.w_fixnum):
            selector = mapdict.INT_ATTR
        elif space.is_kind_of(w_value, space.w_float):
            selector = mapdict.FLOAT_ATTR
        else:
            selector = mapdict.OBJECT_ATTR
        idx, tp = jit.promote(self.map).read(selector, name)

        if idx == mapdict.ATTR_DOES_NOT_EXIST or idx == mapdict.ATTR_WRONG_TYPE:
            self.map, idx = self.map.add(space, selector, name, self)

        if selector == mapdict.INT_ATTR:
            self.unboxed_storage[idx] = longlong2float.longlong2float(space.int_w(w_value))
        elif selector == mapdict.FLOAT_ATTR:
            self.unboxed_storage[idx] = space.float_w(w_value)
        elif selector == mapdict.OBJECT_ATTR:
            self.object_storage[idx] = w_value
        else:
            raise SystemError

    def copy_instance_vars(self, space, w_other):
        assert isinstance(w_other, W_Object)
        w_other.map.copy_attrs(space, w_other, self)

    def get_flag(self, space, name):
        idx = jit.promote(self.map).read(mapdict.FLAG, name)
        if idx == mapdict.ATTR_DOES_NOT_EXIST:
            return space.w_false
        return self.object_storage[idx]

    def set_flag(self, space, name):
        idx = jit.promote(self.map).read(mapdict.FLAG, name)
        if idx == mapdict.ATTR_DOES_NOT_EXIST:
            self.map, idx = self.map.add(space, mapdict.FLAG, name, self)
        self.object_storage[idx] = space.w_true

    def unset_flag(self, space, name):
        idx = jit.promote(self.map).read(mapdict.FLAG, name)
        if idx != mapdict.ATTR_DOES_NOT_EXIST:
            # Flags are by default unset, no need to add if unsetting
            self.object_storage[idx] = space.w_false
