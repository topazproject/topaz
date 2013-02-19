from topaz.module import ClassDef, check_frozen
from topaz.modules.enumerable import Enumerable
from topaz.objects.objectobject import W_Object
from topaz.utils.ordereddict import OrderedDict


class W_HashObject(W_Object):
    classdef = ClassDef("Hash", W_Object.classdef, filepath=__file__)
    classdef.include_module(Enumerable)

    def __init__(self, space, klass=None):
        W_Object.__init__(self, space, klass)
        self.contents = OrderedDict(space.eq_w, space.hash_w)
        self.w_default = space.w_nil
        self.default_proc = None

    @classdef.singleton_method("allocate")
    def method_allocate(self, space, args_w):
        return W_HashObject(space, self)

    @classdef.singleton_method("[]")
    def singleton_method_subscript(self, space, w_obj=None):
        if w_obj is None:
            return W_HashObject(space)
        w_res = space.convert_type(w_obj, space.w_hash, "to_hash", raise_error=False)
        if w_res is space.w_nil:
            raise NotImplementedError
        assert isinstance(w_res, W_HashObject)
        result = W_HashObject(space)
        result.contents.update(w_res.contents)
        return result

    @classdef.method("initialize")
    def method_initialize(self, space, w_default=None, block=None):
        if w_default is not None:
            self.w_default = w_default
        if block is not None:
            self.default_proc = block

    @classdef.method("default")
    def method_default(self, space, w_key=None):
        if self.default_proc is not None:
            return space.invoke_block(self.default_proc, [self, w_key])
        else:
            return self.w_default

    @classdef.method("[]")
    def method_subscript(self, space, w_key):
        try:
            return self.contents[w_key]
        except KeyError:
            return space.send(self, space.newsymbol("default"), [w_key])

    @classdef.method("fetch")
    def method_fetch(self, space, w_key, w_value=None, block=None):
        try:
            return self.contents[w_key]
        except KeyError:
            if w_value is not None:
                return w_value
            elif block is not None:
                return space.invoke_block(block, [w_key])
            else:
                raise space.error(space.w_KeyError, "key not found: %s" % space.send(w_key, space.newsymbol("inspect")))

    @classdef.method("store")
    @classdef.method("[]=")
    def method_subscript_assign(self, w_key, w_value):
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
            return space.send(self, space.newsymbol("default"))
        w_key, w_value = self.contents.popitem()
        return space.newarray([w_key, w_value])

    @classdef.method("initialize_copy")
    @classdef.method("replace")
    @check_frozen()
    def method_replace(self, space, w_hash):
        assert isinstance(w_hash, W_HashObject)
        self.contents.clear()
        self.contents.update(w_hash.contents)
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
    classdef = ClassDef("HashIterator", W_Object.classdef, filepath=__file__)

    def __init__(self, space, d):
        W_Object.__init__(self, space)
        self.iterator = d.iteritems()

    @classdef.singleton_method("allocate")
    def method_allocate(self, space, w_obj):
        assert isinstance(w_obj, W_HashObject)
        return W_HashIterator(space, w_obj.contents)

    @classdef.method("initialize")
    def method_initialize(self, w_obj):
        pass

    @classdef.method("next")
    def method_next(self, space):
        try:
            w_k, w_v = self.iterator.next()
        except StopIteration:
            raise space.error(space.w_StopIteration)
        return space.newarray([w_k, w_v])
