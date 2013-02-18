import copy

from rpython.rlib.listsort import TimSort

from topaz.coerce import Coerce
from topaz.module import ClassDef, check_frozen
from topaz.modules.enumerable import Enumerable
from topaz.objects.objectobject import W_Object
from topaz.utils.packing.pack import RPacker


class RubySorter(TimSort):
    def __init__(self, space, list, listlength=None, sortblock=None):
        TimSort.__init__(self, list, listlength=listlength)
        self.space = space
        self.sortblock = sortblock

    def lt(self, a, b):
        if self.sortblock is None:
            w_cmp_res = self.space.send(a, self.space.newsymbol("<=>"), [b])
        else:
            w_cmp_res = self.space.invoke_block(self.sortblock, [a, b])
        if w_cmp_res is self.space.w_nil:
            raise self.space.error(
                self.space.w_ArgumentError,
                "comparison of %s with %s failed" % (self.space.getclass(a).name, self.space.getclass(b).name)
            )
        else:
            return self.space.int_w(w_cmp_res) < 0


class W_ArrayObject(W_Object):
    classdef = ClassDef("Array", W_Object.classdef, filepath=__file__)
    classdef.include_module(Enumerable)

    def __init__(self, space, items_w):
        W_Object.__init__(self, space)
        self.items_w = items_w

    def __deepcopy__(self, memo):
        obj = super(W_ArrayObject, self).__deepcopy__(memo)
        obj.items_w = copy.deepcopy(self.items_w, memo)
        return obj

    def listview(self, space):
        return self.items_w

    @classdef.singleton_method("allocate")
    def singleton_method_allocate(self, space):
        return space.newarray([])

    @classdef.singleton_method("[]")
    def singleton_method_subscript(self, space, args_w):
        return space.newarray(args_w)

    @classdef.method("initialize_copy", other_w="array")
    @classdef.method("replace", other_w="array")
    @check_frozen()
    def method_replace(self, space, other_w):
        del self.items_w[:]
        self.items_w.extend(other_w)
        return self

    @classdef.method("at")
    @classdef.method("[]")
    @classdef.method("slice")
    def method_subscript(self, space, w_idx, w_count=None):
        start, end, as_range, nil = space.subscript_access(len(self.items_w), w_idx, w_count=w_count)
        if nil:
            return space.w_nil
        elif as_range:
            assert start >= 0
            assert end >= 0
            return space.newarray(self.items_w[start:end])
        else:
            return self.items_w[start]

    @classdef.method("[]=")
    def method_subscript_assign(self, space, w_idx, w_count_or_obj, w_obj=None):
        w_count = None
        if w_obj:
            w_count = w_count_or_obj
        else:
            w_obj = w_count_or_obj
        start, end, as_range, nil = space.subscript_access(len(self.items_w), w_idx, w_count=w_count)

        if w_count and end < start:
            raise space.error(space.w_IndexError,
                "negative length (%d)" % (end - start)
            )
        elif start < 0:
            raise space.error(space.w_IndexError,
                "index %d too small for array; minimum: %d" % (
                    start - len(self.items_w),
                    -len(self.items_w)
                )
            )
        elif start >= len(self.items_w):
            self.items_w += [space.w_nil] * (start - len(self.items_w) + 1)
            self.items_w[start] = w_obj
        elif as_range:
            assert end >= 0
            w_converted = space.convert_type(w_obj, space.w_array, "to_ary", raise_error=False)
            if w_converted is space.w_nil:
                rep_w = [w_obj]
            else:
                rep_w = space.listview(w_converted)
            delta = (end - start) - len(rep_w)
            if delta < 0:
                self.items_w += [None] * -delta
                lim = start + len(rep_w)
                i = len(self.items_w) - 1
                while i >= lim:
                    self.items_w[i] = self.items_w[i + delta]
                    i -= 1
            elif delta > 0:
                del self.items_w[start:start + delta]
            self.items_w[start:start + len(rep_w)] = rep_w
        else:
            self.items_w[start] = w_obj
        return w_obj

    @classdef.method("slice!")
    @check_frozen()
    def method_slice_i(self, space, w_idx, w_count=None):
        start, end, as_range, nil = space.subscript_access(len(self.items_w), w_idx, w_count=w_count)

        if nil:
            return space.w_nil
        elif as_range:
            start = min(max(start, 0), len(self.items_w))
            end = min(max(end, 0), len(self.items_w))
            delta = (end - start)
            assert delta >= 0
            w_items = self.items_w[start:start + delta]
            del self.items_w[start:start + delta]
            return space.newarray(w_items)
        else:
            w_item = self.items_w[start]
            del self.items_w[start]
            return w_item

    @classdef.method("size")
    @classdef.method("length")
    def method_length(self, space):
        return space.newint(len(self.items_w))

    @classdef.method("empty?")
    def method_emptyp(self, space):
        return space.newbool(len(self.items_w) == 0)

    @classdef.method("+", other="array")
    def method_add(self, space, other):
        return space.newarray(self.items_w + other)

    @classdef.method("<<")
    @check_frozen()
    def method_lshift(self, space, w_obj):
        self.items_w.append(w_obj)
        return self

    @classdef.method("concat", other="array")
    @check_frozen()
    def method_concat(self, space, other):
        self.items_w += other
        return self

    @classdef.method("push")
    @check_frozen()
    def method_push(self, space, args_w):
        self.items_w.extend(args_w)
        return self

    @classdef.method("shift")
    @check_frozen()
    def method_shift(self, space, w_n=None):
        if w_n is None:
            if self.items_w:
                return self.items_w.pop(0)
            else:
                return space.w_nil
        n = space.int_w(space.convert_type(w_n, space.w_fixnum, "to_int"))
        if n < 0:
            raise space.error(space.w_ArgumentError, "negative array size")
        items_w = self.items_w[:n]
        del self.items_w[:n]
        return space.newarray(items_w)

    @classdef.method("unshift")
    @check_frozen()
    def method_unshift(self, space, args_w):
        for i in xrange(len(args_w) - 1, -1, -1):
            w_obj = args_w[i]
            self.items_w.insert(0, w_obj)
        return self

    @classdef.method("join")
    def method_join(self, space, w_sep=None):
        if not self.items_w:
            return space.newstr_fromstr("")
        if w_sep is None:
            separator = ""
        elif space.respond_to(w_sep, space.newsymbol("to_str")):
            separator = space.str_w(space.send(w_sep, space.newsymbol("to_str")))
        else:
            raise space.error(space.w_TypeError,
                "can't convert %s into String" % space.getclass(w_sep).name
            )
        return space.newstr_fromstr(separator.join([
            space.str_w(space.send(w_o, space.newsymbol("to_s")))
            for w_o in self.items_w
        ]))

    @classdef.singleton_method("try_convert")
    def method_try_convert(self, space, w_obj):
        if not space.is_kind_of(w_obj, space.w_array):
            w_obj = space.convert_type(w_obj, space.w_array, "to_ary", raise_error=False)
        return w_obj

    @classdef.method("pop")
    def method_pop(self, space, w_num=None):
        if w_num is None:
            if self.items_w:
                return self.items_w.pop()
            else:
                return space.w_nil
        else:
            num = space.int_w(space.convert_type(
                w_num, space.w_fixnum, "to_int"
            ))
            if num < 0:
                raise space.error(space.w_ArgumentError, "negative array size")
            else:
                pop_size = max(0, len(self.items_w) - num)
                res_w = self.items_w[pop_size:]
                del self.items_w[pop_size:]
                return space.newarray(res_w)

    @classdef.method("delete_at", idx="int")
    @check_frozen()
    def method_delete_at(self, space, idx):
        if idx < 0:
            idx += len(self.items_w)
        if idx < 0 or idx >= len(self.items_w):
            return space.w_nil
        else:
            return self.items_w.pop(idx)

    @classdef.method("last")
    def method_last(self, space, w_count=None):
        if w_count is not None:
            count = Coerce.int(space, w_count)
            if count < 0:
                raise space.error(space.w_ArgumentError, "negative array size")
            start = len(self.items_w) - count
            if start < 0:
                start = 0
            return space.newarray(self.items_w[start:])

        if len(self.items_w) == 0:
            return space.w_nil
        else:
            return self.items_w[len(self.items_w) - 1]

    @classdef.method("pack", template="str")
    def method_pack(self, space, template):
        result = RPacker(template, space.listview(self)).operate(space)
        return space.newstr_fromchars(result)

    @classdef.method("to_ary")
    def method_to_ary(self, space):
        return self

    @classdef.method("clear")
    @check_frozen()
    def method_clear(self, space):
        del self.items_w[:]
        return self

    @classdef.method("sort!")
    def method_sort(self, space, block):
        RubySorter(space, self.items_w, sortblock=block).sort()
        return self
