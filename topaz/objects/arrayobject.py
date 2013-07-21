import copy

from rpython.rlib import jit
from rpython.rlib.listsort import make_timsort_class
from rpython.rlib.rerased import new_static_erasing_pair
from rpython.rlib.rbigint import rbigint

from topaz.coerce import Coerce
from topaz.module import ClassDef, check_frozen
from topaz.modules.enumerable import Enumerable
from topaz.objects.objectobject import W_Object
from topaz.utils.packing.pack import RPacker


BaseRubySorter = make_timsort_class()
BaseRubySortBy = make_timsort_class()


class RubySorter(BaseRubySorter):
    def __init__(self, space, list, listlength=None, sortblock=None):
        BaseRubySorter.__init__(self, list, listlength=listlength)
        self.space = space
        self.sortblock = sortblock

    def lt(self, w_a, w_b):
        w_cmp_res = self.space.compare(w_a, w_b, self.sortblock)
        if self.space.is_kind_of(w_cmp_res, self.space.w_bignum):
            return self.space.bigint_w(w_cmp_res).lt(rbigint.fromint(0))
        else:
            return self.space.int_w(w_cmp_res) < 0


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


class BaseArrayStrategy(object):
    def __init__(self, space):
        pass

    def switch_to_object_strategy(self, space, w_ary):
        obj_strategy = space.fromcache(ObjectArrayStrategy)
        w_ary.array_storage = obj_strategy.erase(self.listview(space, w_ary))
        w_ary.strategy = obj_strategy


class TypedArrayStrategyMixin(object):
    _mixin_ = True

    def get_empty_storage(self):
        return self.erase([])

    def length(self, w_ary):
        return len(self.unerase(w_ary.array_storage))

    def getitem(self, space, w_ary, idx):
        return self.wrap(space, self.unerase(w_ary.array_storage)[idx])

    def getslice(self, space, w_ary, start, end):
        return self.erase(self.unerase(w_ary.array_storage)[start:end])

    def setitem(self, space, w_ary, idx, w_obj):
        if self.is_correct_type(space, w_obj):
            self.unerase(w_ary.array_storage)[idx] = self.unwrap(space, w_obj)
        else:
            self.switch_to_object_strategy(space, w_ary)
            w_ary.strategy.setitem(space, w_ary, idx, w_obj)

    def delslice(self, space, w_ary, start, end):
        del self.unerase(w_ary.array_storage)[start:end]

    def append(self, space, w_ary, w_obj):
        if self.is_correct_type(space, w_obj):
            self.unerase(w_ary.array_storage).append(self.unwrap(space, w_obj))
        else:
            self.switch_to_object_strategy(space, w_ary)
            w_ary.append(space, w_obj)

    def append_empty(self, w_ary):
        self.unerase(w_ary.array_storage).append(self.empty_value)

    def extend(self, space, w_ary, other_w):
        for w_o in other_w:
            w_ary.append(space, w_o)

    def extend_from_storage(self, space, w_ary, data):
        self.unerase(w_ary.array_storage).extend(self.unerase(data))

    def insert(self, space, w_ary, idx, w_obj):
        if self.is_correct_type(space, w_obj):
            self.unerase(w_ary.array_storage).insert(idx, self.unwrap(space, w_obj))
        else:
            self.switch_to_object_strategy(space, w_ary)
            w_ary.strategy.insert(space, w_ary, idx, w_obj)

    def listview(self, space, w_ary):
        return [self.wrap(space, item) for item in self.unerase(w_ary.array_storage)]

    def pop(self, space, w_ary, idx):
        storage = self.unerase(w_ary.array_storage)
        return self.wrap(space, storage.pop(idx))

    def reverse(self, space, w_ary):
        storage = self.unerase(w_ary.array_storage)
        storage.reverse()

    def clear(self, space, w_ary):
        del self.unerase(w_ary.array_storage)[:]

    def mul(self, w_ary, n):
        return self.erase(self.unerase(w_ary.array_storage) * n)

    def sort(self, space, w_ary, block):
        # TODO: this should use an unboxed sorter if <=> has not been
        # overwritten on the appropriate type
        self.switch_to_object_strategy(space, w_ary)
        w_ary.strategy.sort(space, w_ary, block)

    def sort_by(self, space, w_ary, block):
        raise space.error(space.w_NotImplementedError, "Array#sort_by")

    def wrap(self, space, w_obj):
        raise NotImplementedError

    def unwrap(self, space, w_obj):
        raise NotImplementedError

    def erase(self, items):
        raise NotImplementedError

    def unerase(self, items):
        raise NotImplementedError


class ObjectArrayStrategy(BaseArrayStrategy, TypedArrayStrategyMixin):
    erase, unerase = new_static_erasing_pair("object")
    empty_value = None

    def wrap(self, space, w_obj):
        return w_obj

    def unwrap(self, space, w_obj):
        return w_obj

    def is_correct_type(self, space, w_obj):
        return True

    def listview(self, space, w_ary):
        return self.unerase(w_ary.array_storage)

    def extend(self, space, w_ary, other_w):
        self.unerase(w_ary.array_storage).extend(other_w)

    def sort(self, space, w_ary, block):
        RubySorter(space, self.unerase(w_ary.array_storage), sortblock=block).sort()


class FloatArrayStrategy(BaseArrayStrategy, TypedArrayStrategyMixin):
    erase, unerase = new_static_erasing_pair("FloatArrayStrategy")
    empty_value = 0.0

    def wrap(self, space, f):
        return space.newfloat(f)

    def unwrap(self, space, w_f):
        return space.float_w(w_f)

    def is_correct_type(self, space, w_obj):
        return space.is_kind_of(w_obj, space.w_float)


class FixnumArrayStrategy(BaseArrayStrategy, TypedArrayStrategyMixin):
    erase, unerase = new_static_erasing_pair("FixnumArrayStrategy")
    empty_value = 0

    def wrap(self, space, i):
        return space.newint(i)

    def unwrap(self, space, w_i):
        return space.int_w(w_i)

    def is_correct_type(self, space, w_obj):
        return space.is_kind_of(w_obj, space.w_fixnum)


class EmptyArrayStrategy(BaseArrayStrategy):
    erase, unerase = new_static_erasing_pair("EmptyArrayStrategy")

    def switch_to_correct_strategy(self, space, w_ary, w_obj):
        if space.is_kind_of(w_obj, space.w_fixnum):
            strategy = space.fromcache(FixnumArrayStrategy)
        elif space.is_kind_of(w_obj, space.w_float):
            strategy = space.fromcache(FloatArrayStrategy)
        else:
            strategy = space.fromcache(ObjectArrayStrategy)
        w_ary.strategy = strategy
        w_ary.array_storage = strategy.get_empty_storage()

    def get_empty_storage(self):
        return self.erase(None)

    def length(self, w_ary):
        return 0

    def listview(self, space, w_ary):
        return []

    def is_correct_type(self, w_obj):
        return False

    def append(self, space, w_ary, w_obj):
        self.switch_to_correct_strategy(space, w_ary, w_obj)
        w_ary.strategy.append(space, w_ary, w_obj)

    def insert(self, space, w_ary, idx, w_obj):
        self.append(space, w_ary, w_obj)

    def extend(self, space, w_ary, other_w):
        if not other_w:
            return
        strategy = W_ArrayObject.strategy_for_list(space, other_w)
        w_ary.strategy = strategy
        w_ary.array_storage = strategy.get_empty_storage()
        w_ary.strategy.extend(space, w_ary, other_w)

    def clear(self, space, w_ary):
        pass

    def sort(self, space, w_ary, block):
        pass


class W_ArrayObject(W_Object):
    classdef = ClassDef("Array", W_Object.classdef)
    classdef.include_module(Enumerable)

    def __init__(self, space, strategy, storage, klass=None):
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

    def append(self, space, w_obj):
        self.strategy.append(space, self, w_obj)

    @staticmethod
    def newarray(space, items_w):
        strategy = space.fromcache(EmptyArrayStrategy)
        w_ary = W_ArrayObject(space, strategy, strategy.get_empty_storage())
        w_ary.strategy.extend(space, w_ary, items_w)
        return w_ary

    @staticmethod
    def strategy_for_list(space, items_w):
        if not items_w:
            return space.fromcache(EmptyArrayStrategy)

        for w_item in items_w:
            if not space.is_kind_of(w_item, space.w_fixnum):
                break
        else:
            return space.fromcache(FixnumArrayStrategy)

        for w_item in items_w:
            if not space.is_kind_of(w_item, space.w_float):
                break
        else:
            return space.fromcache(FloatArrayStrategy)

        return space.fromcache(ObjectArrayStrategy)

    @classdef.singleton_method("allocate")
    def singleton_method_allocate(self, space):
        strategy = space.fromcache(EmptyArrayStrategy)
        return W_ArrayObject(space, strategy, strategy.get_empty_storage(), self)

    def replace(self, space, other_w):
        self.strategy = W_ArrayObject.strategy_for_list(space, other_w)
        self.array_storage = self.strategy.get_empty_storage()
        self.strategy.extend(space, self, other_w)

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
            data = self.strategy.getslice(space, self, start, end)
            return W_ArrayObject(space, self.strategy, data, space.getnonsingletonclass(self))
        else:
            return self.strategy.getitem(space, self, start)

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
            self.strategy.extend(space, self, [space.w_nil] * (start - self.length() + 1))
            self.strategy.setitem(space, self, start, w_obj)
        elif as_range:
            w_converted = space.convert_type(w_obj, space.w_array, "to_ary", raise_error=False)
            if w_converted is space.w_nil:
                rep_w = [w_obj]
            else:
                rep_w = space.listview(w_converted)
            self._subscript_assign_range(space, start, end, rep_w)
        else:
            self.strategy.setitem(space, self, start, w_obj)
        return w_obj

    def _subscript_assign_range(self, space, start, end, rep_w):
        assert end >= 0
        delta = (end - start) - len(rep_w)
        if delta < 0:
            for i in xrange(-delta):
                self.strategy.append_empty(self)
            lim = start + len(rep_w)
            i = self.length() - 1
            while i >= lim:
                self.strategy.setitem(space, self, i, self.strategy.getitem(space, self, i + delta))
                i -= 1
        elif delta > 0:
            self.strategy.delslice(space, self, start, start + delta)
        for i, w_obj in enumerate(rep_w):
            self.strategy.setitem(space, self, i + start, w_obj)

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
            data = self.strategy.getslice(space, self, start, start + delta)
            self.strategy.delslice(space, self, start, start + delta)
            return W_ArrayObject(space, self.strategy, data)
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
        self.append(space, w_obj)
        return self

    @classdef.method("concat", other_w="array")
    @check_frozen()
    def method_concat(self, space, other_w):
        self.strategy.extend(space, self, other_w)
        return self

    @classdef.method("*")
    def method_times(self, space, w_other):
        if space.respond_to(w_other, "to_str"):
            return space.send(self, "join", [w_other])
        n = space.int_w(space.convert_type(w_other, space.w_fixnum, "to_int"))
        if n < 0:
            raise space.error(space.w_ArgumentError, "Count cannot be negative")
        w_res = W_ArrayObject(space, self.strategy, self.strategy.mul(self, n), space.getnonsingletonclass(self))
        space.infect(w_res, self, freeze=False)
        return w_res

    @classdef.method("push")
    @check_frozen()
    def method_push(self, space, args_w):
        self.strategy.extend(space, self, args_w)
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
        data = self.strategy.getslice(space, self, 0, n)
        self.strategy.delslice(space, self, 0, n)
        return W_ArrayObject(space, self.strategy, data)

    @classdef.method("unshift")
    @check_frozen()
    def method_unshift(self, space, args_w):
        for w_obj in reversed(args_w):
            self.strategy.insert(space, self, 0, w_obj)
        return self

    @classdef.method("join")
    def method_join(self, space, w_sep=None):
        if not self.length():
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
            space.str_w(space.send(w_o, "to_s"))
            for w_o in self.listview(space)
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
                pop_size = max(0, self.length() - num)
                data = self.strategy.getslice(space, self, pop_size, self.length())
                self.strategy.delslice(space, self, pop_size, self.length())
                return W_ArrayObject(space, self.strategy, data)
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
            return self.strategy.getitem(space, self, self.length() - 1)

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
        self.strategy.sort(space, self, block)
        return self

    @classdef.method("sort_by!")
    @check_frozen()
    def method_sort_by_i(self, space, block):
        if block is None:
            return space.send(self, "enum_for", [space.newsymbol("sort_by!")])
        self.strategy.sort_by(space, self, block)
        return self

    @classdef.method("reverse!")
    @check_frozen()
    def method_reverse_i(self, space):
        self.strategy.reverse(space, self)
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
        self.strategy.extend_from_storage(space, self, self.strategy.getslice(space, self, 0, n))
        self.strategy.delslice(space, self, 0, n)
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
            self.strategy.extend(space, self, args_w)
            return self
        if i < 0:
            if i < -length - 1:
                raise space.error(space.w_IndexError,
                    "index %d too small for array; minimum: %d" % (i + 1, -length)
                )
            i += length + 1
        assert i >= 0
        for w_e in args_w:
            self.strategy.insert(space, self, i, w_e)
            i += 1
        return self

    def _append_nils(self, space, num):
        for _ in xrange(num):
            self.append(space, space.w_nil)
