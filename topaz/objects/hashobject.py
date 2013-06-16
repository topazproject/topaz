from topaz.module import ClassDef, check_frozen
from topaz.modules.enumerable import Enumerable
from topaz.objects.objectobject import W_Object
from topaz.utils.ordereddict import OrderedDict
from topaz.objects.procobject import W_ProcObject


class W_HashObject(W_Object):
    classdef = ClassDef("Hash", W_Object.classdef)
    classdef.include_module(Enumerable)

    def __init__(self, space, klass=None):
        W_Object.__init__(self, space, klass)
        self.contents = OrderedDict(space.eq_w, space.hash_w)
        self.w_default = space.w_nil
        self.default_proc = None

    @classdef.singleton_method("allocate")
    def method_allocate(self, space):
        return W_HashObject(space, self)

    @classdef.method("initialize")
    @check_frozen()
    def method_initialize(self, space, w_default=None, block=None):
        if w_default is not None:
            if block is not None:
                raise space.error(space.w_ArgumentError, "wrong number of arguments")
            self.w_default = w_default
        if block is not None:
            self.default_proc = block
        return self

    @classdef.method("default")
    def method_default(self, space, w_key=None):
        if self.default_proc is not None and w_key is not None:
            return space.invoke_block(self.default_proc, [self, w_key])
        else:
            return self.w_default

    @classdef.method("default=")
    @check_frozen()
    def method_set_default(self, space, w_defl):
        self.default_proc = None
        self.w_default = w_defl

    @classdef.method("default_proc")
    def method_default_proc(self, space):
        if self.default_proc is None:
            return space.w_nil
        return self.default_proc

    @classdef.method("default_proc=")
    def method_set_default_proc(self, space, w_proc):
        w_new_proc = space.convert_type(w_proc, space.w_proc, "to_proc")
        assert isinstance(w_new_proc, W_ProcObject)
        arity = space.int_w(space.send(w_new_proc, "arity"))
        if arity != 2 and space.is_true(space.send(w_new_proc, "lambda?")):
            raise space.error(space.w_TypeError, "default_proc takes two arguments (2 for %s)" % arity)
        self.default_proc = w_new_proc
        self.w_default = space.w_nil
        return w_proc

    @classdef.method("[]")
    def method_subscript(self, space, w_key):
        try:
            return self.contents[w_key]
        except KeyError:
            return space.send(self, "default", [w_key])

    @classdef.method("fetch")
    def method_fetch(self, space, w_key, w_value=None, block=None):
        try:
            return self.contents[w_key]
        except KeyError:
            if block is not None:
                return space.invoke_block(block, [w_key])
            elif w_value is not None:
                return w_value
            else:
                raise space.error(space.w_KeyError, "key not found: %s" % space.send(w_key, "inspect"))

    @classdef.method("store")
    @classdef.method("[]=")
    @check_frozen()
    def method_subscript_assign(self, space, w_key, w_value):
        if (space.is_kind_of(w_key, space.w_string) and
            not space.is_true(space.send(w_key, "frozen?"))):

            w_key = space.send(w_key, "dup")
            w_key = space.send(w_key, "freeze")
        self.contents[w_key] = w_value
        return w_value

    @classdef.method("length")
    @classdef.method("size")
    def method_size(self, space):
        return space.newint(len(self.contents))

    @classdef.method("empty?")
    def method_emptyp(self, space):
        return space.newbool(not bool(self.contents))

    @classdef.method("delete")
    @check_frozen()
    def method_delete(self, space, w_key, block):
        w_res = self.contents.pop(w_key, None)
        if w_res is None:
            if block:
                return space.invoke_block(block, [w_key])
            w_res = space.w_nil
        return w_res

    @classdef.method("clear")
    @check_frozen()
    def method_clear(self, space):
        self.contents.clear()
        return self

    @classdef.method("shift")
    @check_frozen()
    def method_shift(self, space):
        if not self.contents:
            return space.send(self, "default", [space.w_nil])
        w_key, w_value = self.contents.popitem()
        return space.newarray([w_key, w_value])

    @classdef.method("initialize_copy")
    @classdef.method("replace")
    @check_frozen()
    def method_replace(self, space, w_hash):
        w_hash = space.convert_type(w_hash, space.w_hash, "to_hash")
        assert isinstance(w_hash, W_HashObject)
        self.contents.clear()
        self.contents.update(w_hash.contents)
        self.w_default = w_hash.w_default
        self.default_proc = w_hash.default_proc
        return self

    @classdef.method("keys")
    def method_keys(self, space):
        return space.newarray(self.contents.keys())

    @classdef.method("values")
    def method_values(self, space):
        return space.newarray(self.contents.values())

    @classdef.method("to_hash")
    def method_to_hash(self, space):
        return self

    @classdef.method("key?")
    @classdef.method("has_key?")
    @classdef.method("member?")
    @classdef.method("include?")
    def method_includep(self, space, w_key):
        return space.newbool(w_key in self.contents)


class W_HashIterator(W_Object):
    classdef = ClassDef("HashIterator", W_Object.classdef)

    def __init__(self, space):
        W_Object.__init__(self, space)

    @classdef.singleton_method("allocate")
    def method_allocate(self, space):
        return W_HashIterator(space)

    @classdef.method("initialize")
    def method_initialize(self, w_obj):
        assert isinstance(w_obj, W_HashObject)
        self.iterator = w_obj.contents.iteritems()
        return self

    @classdef.method("next")
    def method_next(self, space):
        try:
            w_k, w_v = self.iterator.next()
        except StopIteration:
            raise space.error(space.w_StopIteration)
        return space.newarray([w_k, w_v])
