import copy

from rpython.rlib import jit
from rpython.rlib.listsort import TimSort
from rpython.rlib.listsort import make_timsort_class
from rpython.rlib.rerased import new_static_erasing_pair
from rpython.rlib.rbigint import rbigint

from topaz.coerce import Coerce
from topaz.module import ClassDef, check_frozen
from topaz.modules.enumerable import Enumerable
from topaz.objects.objectobject import W_Object
from topaz.utils.packing.pack import RPacker
from topaz.objects.floatobject import W_FloatObject
from topaz.objects.intobject import W_FixnumObject


BaseRubySorter = make_timsort_class()
BaseRubySortBy = make_timsort_class()


class RubySorter(BaseRubySorter):
    def __init__(self, space, list, listlength=None, sortblock=None):
        BaseRubySorter.__init__(self, list, listlength=listlength)
        self.space = space
        self.sortblock = sortblock

    def lt(self, w_a, w_b):
        # NOTE(flaper87): Review
        if self.sortblock is None:
            w_cmp_res = self.space.send(w_a, self.space.newsymbol("<=>"), [w_b])
        else:
            w_cmp_res = self.space.invoke_block(self.sortblock, [w_a, w_b])
        if w_cmp_res is self.space.w_nil:
            raise self.space.error(
                self.space.w_ArgumentError,
                "comparison of %s with %s failed" %
                (self.space.obj_to_s(self.space.getclass(w_a)),
                   self.space.obj_to_s(self.space.getclass(w_b)))
            )
        else:
            return self.space.int_w(w_cmp_res) < 0
        #w_cmp_res = self.space.compare(w_a, w_b, self.sortblock)
        #if self.space.is_kind_of(w_cmp_res, self.space.w_bignum):
        #    return self.space.bigint_w(w_cmp_res).lt(rbigint.fromint(0))
        #else:
        #    return self.space.int_w(w_cmp_res) < 0


class RubySortBy(BaseRubySortBy):
    def __init__(self, space, list, listlength=None, sortblock=None):
        BaseRubySortBy.__init__(self, list, listlength=listlength)
        self.space = space
        self.sortblock = sortblock

    def lt(self, w_a, w_b):
        w_cmp_res = self.space.compare(
            self.space.invoke_block(self.sortblock, [w_a]),
            self.space.invoke_block(self.sortblock, [w_b])
        )
        return self.space.int_w(w_cmp_res) < 0


class ArrayStrategy(object):
    def __init__(self, space):
        pass

    def __deepcopy__(self, memo):
        memo[id(self)] = result = object.__new__(self.__class__)
        return result

    def append(self, space, w_ary, w_obj):
        raise NotImplementedError

    def checktype(self, w_obj):
        raise NotImplementedError

    def clear(self, space, w_ary):
        self.to_empty_strategy(space, w_ary)

    def extend(self, space, w_ary, other_w):
        raise NotImplementedError

    def get_item(self, space, w_ary, idx):
        raise NotImplementedError

    def insert(self, space, w_ary, idx, w_obj):
        raise NotImplementedError

    def length(self, w_ary):
        raise NotImplementedError

    def listview(self, space, w_ary):
        raise NotImplementedError

    def padd_assign(self, space, w_ary, delta, start, end, rep_w):
        raise NotImplementedError

    def pop(self, space, w_ary, idx):
        raise NotImplementedError

    def pop_n(self, space, w_ary, num):
        raise NotImplementedError

    def reverse_i(self, space, w_ary):
        raise NotImplementedError

    def set_item(self, space, w_ary, idx, w_obj):
        raise NotImplementedError

    def slice(self, space, w_ary, start, end):
        raise NotImplementedError

    def slice_i(self, space, w_ary, start, end):
        raise NotImplementedError

    def adapt(self, space, w_ary, w_obj):
        if not self.checktype(w_obj):
            self.to_object_strategy(space, w_ary)

    def to_object_strategy(self, space, w_ary):
        obj_strategy = space.fromcache(ObjectArrayStrategy)
        w_ary.array_storage = obj_strategy.erase(self.listview(space, w_ary))
        w_ary.strategy = obj_strategy

    def to_empty_strategy(self, space, w_ary):
        w_ary.strategy = space.fromcache(EmptyArrayStrategy)
        w_ary.array_storage = w_ary.strategy.erase(None)


class ErasingArrayStrategyMixin(object):
    _mixin_ = True

    def append(self, space, w_ary, w_obj):
        self.unerase(w_ary.array_storage).append(self.unwrap(space, w_obj))

    def extend(self, space, w_ary, other_w):
        self.unerase(w_ary.array_storage).extend([self.unwrap(space, w_o) for w_o in other_w])

    def get_item(self, space, w_ary, idx):
        return self.wrap(space, self.unerase(w_ary.array_storage)[idx])

    def insert(self, space, w_ary, idx, w_obj):
        self.unerase(w_ary.array_storage).insert(idx, self.unwrap(space, w_obj))

    def length(self, w_ary):
        return len(self.unerase(w_ary.array_storage))

    def listview(self, space, w_ary):
        return [self.wrap(space, item) for item in self.unerase(w_ary.array_storage)]

    def padd_assign(self, space, w_ary, delta, start, end, rep_w):
        storage = self.unerase(w_ary.array_storage)
        if delta < 0:
            storage += [self.padding_value] * -delta
            lim = start + len(rep_w)
            i = len(storage) - 1
            while i >= lim:
                storage[i] = storage[i + delta]
                i -= 1
        elif delta > 0:
            del storage[start:start + delta]
        storage[start:start + len(rep_w)] = [self.unwrap(space, w_obj) for w_obj in rep_w]

    def pop(self, space, w_ary, idx):
        storage = self.unerase(w_ary.array_storage)
        return self.wrap(space, storage.pop(idx))

    def pop_n(self, space, w_ary, num):
        pop_size = max(0, self.length(w_ary) - num)
        return self.slice_i(space, w_ary, pop_size, self.length(w_ary))

    def reverse_i(self, space, w_ary):
        storage = self.unerase(w_ary.array_storage)
        storage.reverse()

    def set_item(self, space, w_ary, idx, w_obj):
        self.unerase(w_ary.array_storage)[idx] = self.unwrap(space, w_obj)

    def slice(self, space, w_ary, start, end):
        items = self.unerase(w_ary.array_storage)[start:end]
        items_w = [self.wrap(space, item) for item in items]
        return space.newarray(items_w)

    def slice_i(self, space, w_ary, start, end):
        w_items = self.slice(space, w_ary, start, end)
        del self.unerase(w_ary.array_storage)[start:end]
        return w_items

    def shift(self, space, w_ary, n):
        return self.slice_i(space, w_ary, 0, n)

    def wrap(self, space, w_obj):
        raise NotImplementedError

    def unwrap(self, space, w_obj):
        raise NotImplementedError

    def store(self, space, items_w):
        raise NotImplementedError

    def erase(self, items):
        raise NotImplementedError

    def unerase(self, items):
        raise NotImplementedError


class ObjectArrayStrategy(ErasingArrayStrategyMixin, ArrayStrategy):
    _erase, _unerase = new_static_erasing_pair("object")
    padding_value = None

    def wrap(self, space, w_obj):
        return w_obj

    def unwrap(self, space, w_obj):
        return w_obj

    def checktype(self, w_obj):
        return True

    def store(self, space, items_w):
        l = [self.unwrap(space, w_o) for w_o in items_w]
        return self.erase(l)

    def erase(self, items):
        return self._erase(items)

    def unerase(self, items):
        return self._unerase(items)

    def to_object_strategy(self, space, w_ary):
        pass

    def listview(self, space, w_ary):
        return self.unerase(w_ary.array_storage)

    def extend(self, space, w_ary, other_w):
        self.unerase(w_ary.array_storage).extend(other_w)


class FloatArrayStrategy(ErasingArrayStrategyMixin, ArrayStrategy):
    _erase, _unerase = new_static_erasing_pair("float")
    padding_value = 0.0

    def wrap(self, space, f):
        return space.newfloat(f)

    def unwrap(self, space, w_f):
        return space.float_w(w_f)

    def checktype(self, w_obj):
        return isinstance(w_obj, W_FloatObject)

    def store(self, space, items_w):
        l = [self.unwrap(space, w_o) for w_o in items_w]
        return self.erase(l)

    def erase(self, items):
        return self._erase(items)

    def unerase(self, items):
        return self._unerase(items)


class FixnumArrayStrategy(ErasingArrayStrategyMixin, ArrayStrategy):
    _erase, _unerase = new_static_erasing_pair("fixnum")
    padding_value = 0

    def wrap(self, space, i):
        return space.newint(i)

    def unwrap(self, space, w_i):
        return space.int_w(w_i)

    def checktype(self, w_obj):
        return isinstance(w_obj, W_FixnumObject)

    def store(self, space, items_w):
        l = [self.unwrap(space, w_o) for w_o in items_w]
        return self.erase(l)

    def erase(self, items):
        return self._erase(items)

    def unerase(self, items):
        return self._unerase(items)


class EmptyArrayStrategy(ArrayStrategy):
    _erase, _unerase = new_static_erasing_pair("empty")

    def length(self, w_ary):
        return 0

    def listview(self, space, w_ary):
        return []

    def checktype(self, w_obj):
        return False

    def store(self, space, items_w):
        return self.erase(None)

    def erase(self, items):
        assert not items
        return self._erase(None)

    def unerase(self, items):
        return self._unerase(items)

    def adapt(self, space, w_ary, w_obj):
        strategy = W_ArrayObject.strategy_for_list(space, [w_obj])
        w_ary.array_storage = strategy.store(space, [])
        w_ary.strategy = strategy

    def to_empty_strategy(self, space, w_ary):
        pass


class W_ArrayObject(W_Object):
    classdef = ClassDef("Array", W_Object.classdef)
    classdef.include_module(Enumerable)

    def __init__(self, space, storage, strategy, klass=None):
        W_Object.__init__(self, space, klass)
        self.strategy = strategy
        self.array_storage = storage

    def __deepcopy__(self, memo):
        obj = super(W_ArrayObject, self).__deepcopy__(memo)
        obj.strategy = copy.deepcopy(self.strategy, memo)
        obj.array_storage = copy.deepcopy(self.array_storage, memo)
        return obj

    def listview(self, space):
        return self.strategy.listview(space, self)

    def length(self):
        return self.strategy.length(self)

    @staticmethod
    def newarray(space, items_w):
        strategy = W_ArrayObject.strategy_for_list(space, items_w)
        storage = strategy.store(space, items_w)
        return W_ArrayObject(space, storage, strategy)

    @staticmethod
    def strategy_for_list(space, items_w):
        if not items_w:
            return space.fromcache(EmptyArrayStrategy)
        else:
            array_type = type(items_w[0])
            for item in items_w:
                if not isinstance(item, array_type):
                    return space.fromcache(ObjectArrayStrategy)
            if array_type is W_FixnumObject:
                return space.fromcache(FixnumArrayStrategy)
            elif array_type is W_FloatObject:
                return space.fromcache(FloatArrayStrategy)
        return space.fromcache(ObjectArrayStrategy)

    def length(self):
        return len(self.items_w)

    @classdef.singleton_method("allocate")
    def singleton_method_allocate(self, space):
        return W_ArrayObject(space, [], self)
        #return space.newarray([])

    def replace(self, space, other_w):
        self.strategy = W_ArrayObject.strategy_for_list(space, other_w)
        self.array_storage = self.strategy.store(space, other_w)

    @classdef.method("initialize_copy", other_w="array")
    @classdef.method("replace", other_w="array")
    @check_frozen()
    def method_replace(self, space, other_w):
        self.replace(space, other_w)
        return self

    @classdef.method("[]")
    @classdef.method("slice")
    def method_subscript(self, space, w_idx, w_count=None):
        start, end, as_range, nil = space.subscript_access(self.length(), w_idx, w_count=w_count)
        if nil:
            return space.w_nil
        elif self.length() == 0:
            return space.newarray([])
        elif as_range:
            assert start >= 0
            assert end >= 0
            return self.strategy.slice(space, self, start, end)
            # NOTE(flaper87): Use the strategy
            #return W_ArrayObject(space, self.items_w[start:end], space.getnonsingletonclass(self))
        else:
            return self.strategy.get_item(space, self, start)

    @classdef.method("[]=")
    @check_frozen()
    def method_subscript_assign(self, space, w_idx, w_count_or_obj, w_obj=None):
        w_count = None
        if w_obj:
            w_count = w_count_or_obj
        else:
            w_obj = w_count_or_obj
        start, end, as_range, _ = space.subscript_access(self.length(), w_idx, w_count=w_count)

        if w_count and end < start:
            raise space.error(space.w_IndexError,
                "negative length (%d)" % (end - start)
            )
        elif start < 0:
            raise space.error(space.w_IndexError,
                "index %d too small for array; minimum: %d" % (
                    start - self.length(),
                    -self.length()
                )
            )
        elif start >= self.length():
            self.strategy.adapt(space, self, space.w_nil)
            self.strategy.extend(space, self, [space.w_nil] * (start - self.length() + 1))
            self.strategy.set_item(space, self, start, w_obj)

            # NOTE(flaper87): Use the strategy
            #self.items_w += [space.w_nil] * (start - self.length() + 1)
            #self.items_w[start] = w_obj
        elif as_range:
            w_converted = space.convert_type(w_obj, space.w_array, "to_ary", raise_error=False)
            if w_converted is space.w_nil:
                rep_w = [w_obj]
            else:
                rep_w = space.listview(w_converted)
            for each in rep_w:
                self.strategy.adapt(space, self, each)
            delta = (end - start) - len(rep_w)
            self.strategy.padd_assign(space, self, delta, start, end, rep_w)
            # NOTE(flaper87): USe the strategy
            #self._subscript_assign_range(space, start, end, rep_w)
        else:
            self.strategy.adapt(space, self, w_obj)
            self.strategy.set_item(space, self, start, w_obj)
        return w_obj

    def _subscript_assign_range(self, space, start, end, rep_w):
        assert end >= 0
        delta = (end - start) - len(rep_w)
        if delta < 0:
            self.items_w += [None] * -delta
            lim = start + len(rep_w)
            i = self.length() - 1
            while i >= lim:
                self.items_w[i] = self.items_w[i + delta]
                i -= 1
        elif delta > 0:
            del self.items_w[start:start + delta]
        self.items_w[start:start + len(rep_w)] = rep_w

    @classdef.method("slice!")
    @check_frozen()
    def method_slice_i(self, space, w_idx, w_count=None):
        start, end, as_range, nil = space.subscript_access(self.length(), w_idx, w_count=w_count)

        if nil:
            return space.w_nil
        elif as_range:
            start = min(max(start, 0), self.length())
            end = min(max(end, 0), self.length())
            delta = (end - start)
            assert delta >= 0
            return self.strategy.slice_i(space, self, start, start + delta)
        else:
            return self.strategy.pop(space, self, start)

    @classdef.method("size")
    @classdef.method("length")
    def method_length(self, space):
        return space.newint(self.length())

    @classdef.method("empty?")
    def method_emptyp(self, space):
        return space.newbool(self.length() == 0)

    @classdef.method("+", other="array")
    def method_add(self, space, other):
        return space.newarray(self.listview(space) + other)

    @classdef.method("<<")
    @check_frozen()
    def method_lshift(self, space, w_obj):
        self.strategy.adapt(space, self, w_obj)
        self.strategy.append(space, self, w_obj)
        return self

    def concat(self, space, other_w):
        strategy = self.strategy_for_list(space, other_w)
        if self.strategy is not strategy:
            self.array_storage = strategy.store(space, self.listview(space))
            self.strategy = strategy
        self.strategy.extend(space, self, other_w)

    @classdef.method("concat", other_w="array")
    @check_frozen()
    def method_concat(self, space, other_w):
        self.concat(space, other_w)
        return self

    @classdef.method("*")
    def method_times(self, space, w_other):
        if space.respond_to(w_other, "to_str"):
            return space.send(self, "join", [w_other])
        n = space.int_w(space.convert_type(w_other, space.w_fixnum, "to_int"))
        if n < 0:
            raise space.error(space.w_ArgumentError, "Count cannot be negative")
        w_res = W_ArrayObject(space, self.items_w * n, space.getnonsingletonclass(self))
        space.infect(w_res, self, freeze=False)
        return w_res

    @classdef.method("push")
    @check_frozen()
    def method_push(self, space, args_w):
        self.concat(space, args_w)
        return self

    @classdef.method("shift")
    @check_frozen()
    def method_shift(self, space, w_n=None):
        if w_n is None:
            if self.length() > 0:
                return self.strategy.pop(space, self, 0)
            else:
                return space.w_nil
        n = space.int_w(space.convert_type(w_n, space.w_fixnum, "to_int"))
        if n < 0:
            raise space.error(space.w_ArgumentError, "negative array size")
        return self.strategy.shift(space, self, n)

    @classdef.method("unshift")
    @check_frozen()
    def method_unshift(self, space, args_w):
        for i in xrange(len(args_w) - 1, -1, -1):
            w_obj = args_w[i]
            self.strategy.adapt(space, self, w_obj)
            self.strategy.insert(space, self, 0, w_obj)
        # NOTE(flaper87): Use strategy,
        # Review this code
        #for w_obj in reversed(args_w):
        #    self.items_w.insert(0, w_obj)
        return self

    @classdef.method("join")
    def method_join(self, space, w_sep=None):
        if not self.listview(space):
            return space.newstr_fromstr("")
        if w_sep is None:
            separator = ""
        elif space.respond_to(w_sep, "to_str"):
            separator = space.str_w(space.send(w_sep, "to_str"))
        else:
            raise space.error(space.w_TypeError,
                "can't convert %s into String" % space.getclass(w_sep).name
            )
        return space.newstr_fromstr(separator.join([
            space.str_w(space.send(w_o, space.newsymbol("to_s")))
            for w_o in self.listview(space)

            # NOTE(flaper87): The above seems right,
            # It iterates over an unreased array and
            # uses the strategy.
            #space.str_w(space.send(w_o, "to_s"))
            #for w_o in self.items_w
        ]))

    @classdef.method("pop")
    @check_frozen()
    def method_pop(self, space, w_num=None):
        if w_num is None:
            if self.length() > 0:
                return self.strategy.pop(space, self, -1)
            else:
                return space.w_nil
        else:
            num = space.int_w(space.convert_type(
                w_num, space.w_fixnum, "to_int"
            ))
            if num < 0:
                raise space.error(space.w_ArgumentError, "negative array size")
            elif self.length() > 0:
                return self.strategy.pop_n(space, self, num)
                # NOTE(flaper87): Use strategy
                #pop_size = max(0, self.length() - num)
                #res_w = self.items_w[pop_size:]
                #del self.items_w[pop_size:]
                #return space.newarray(res_w)
            else:
                return space.newarray([])

    @classdef.method("delete_at", idx="int")
    @check_frozen()
    def method_delete_at(self, space, idx):
        if idx < 0:
            idx += self.length()
        if idx < 0 or idx >= self.length():
            return space.w_nil
        else:
            return self.strategy.pop(space, self, idx)

    @classdef.method("last")
    def method_last(self, space, w_count=None):
        if w_count is not None:
            count = Coerce.int(space, w_count)
            if count < 0:
                raise space.error(space.w_ArgumentError, "negative array size")
            start = self.length() - count
            if start < 0:
                start = 0
            return space.newarray(self.listview(space)[start:])

        if self.length() == 0:
            return space.w_nil
        else:
            return self.listview(space)[self.length() - 1]
            # NOTE(flaper87): The above seems correct and
            # uses strategy's storage
            #return self.items_w[self.length() - 1]

    @classdef.method("pack")
    def method_pack(self, space, w_template):
        template = Coerce.str(space, w_template)
        result = RPacker(template, space.listview(self)).operate(space)
        w_result = space.newstr_fromchars(result)
        space.infect(w_result, w_template)
        return w_result

    @classdef.method("to_ary")
    def method_to_ary(self, space):
        return self

    @classdef.method("clear")
    @check_frozen()
    def method_clear(self, space):
        self.strategy.clear(space, self)
        return self

    @check_frozen()
    @classdef.method("sort!")
    def method_sort_i(self, space, block):
        strategy = self.strategy
        if strategy is space.fromcache(ObjectArrayStrategy):
            RubySorter(space, strategy.unerase(self.array_storage), sortblock=block).sort()
        else:
            items_w = self.listview(space)
            RubySorter(space, items_w, sortblock=block).sort()
            self.replace(space, items_w)
        return self

    @classdef.method("sort_by!")
    @check_frozen()
    def method_sort_by_i(self, space, block):
        if block is None:
            return space.send(self, "enum_for", [space.newsymbol("sort_by!")])
        RubySortBy(space, self.items_w, sortblock=block).sort()
        return self

    @classdef.method("reverse!")
    @check_frozen()
    def method_reverse_i(self, space):
        self.strategy.reverse_i(space, self)
        return self

    @classdef.method("rotate!", n="int")
    @check_frozen()
    def method_rotate_i(self, space, n=1):
        length = self.length()
        if length == 0:
            return self
        if abs(n) >= length:
            n %= length
        if n < 0:
            n += length
        if n == 0:
            return self
        assert n >= 0
        self.items_w.extend(self.items_w[:n])
        del self.items_w[:n]
        return self

    @classdef.method("insert", i="int")
    @check_frozen()
    @jit.look_inside_iff(lambda self, space, i, args_w: jit.isconstant(len(args_w)))
    def method_insert(self, space, i, args_w):
        if not args_w:
            return self
        length = self.length()
        if i > length:
            self._append_nils(space, i - length)
            self.items_w.extend(args_w)
            return self
        if i < 0:
            if i < -length - 1:
                raise space.error(space.w_IndexError,
                    "index %d too small for array; minimum: %d" % (i + 1, -length)
                )
            i += length + 1
        assert i >= 0
        for w_e in args_w:
            self.items_w.insert(i, w_e)
            i += 1
        return self

    def _append_nils(self, space, num):
        for _ in xrange(num):
            self.items_w.append(space.w_nil)
