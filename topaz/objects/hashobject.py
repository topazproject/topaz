from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object
from topaz.utils.ordereddict import OrderedDict


class W_HashObject(W_Object):
    classdef = ClassDef("Hash", W_Object.classdef, filepath=__file__)

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
    def method_delete(self, space, w_key):
        return self.contents.pop(w_key, space.w_nil)

    @classdef.method("keys")
    def method_keys(self, space):
        return space.newarray(self.contents.keys())

    @classdef.method("values")
    def method_values(self, space):
        return space.newarray(self.contents.values())

    @classdef.method("to_hash")
    def method_to_hash(self, space):
        return self

    classdef.app_method("""
    def each
        iter = Topaz::HashIterator.new(self)
        while true
            begin
                key, value = iter.next()
            rescue StopIteration
                return
            end
            yield key, value
        end
    end
    alias each_pair each

    def each_key
        each { |k, v| yield k }
    end
    """)

    @classdef.method("key?")
    @classdef.method("has_key?")
    @classdef.method("member?")
    @classdef.method("include?")
    def method_includep(self, space, w_key):
        return space.newbool(w_key in self.contents)

    classdef.app_method("""
    def ==(other)
        if self.equal?(other)
            return true
        end
        if !other.kind_of?(Hash)
            return false
        end
        if self.size != other.size
            return false
        end
        self.each do |key, value|
            if !other.has_key?(key) || other[key] != value
                return false
            end
        end
        return true
    end
    """)


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
