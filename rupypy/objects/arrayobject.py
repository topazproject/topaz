import struct

from rupypy.module import ClassDef
from rupypy.modules.enumerable import Enumerable
from rupypy.objects.floatobject import W_FloatObject
from rupypy.objects.objectobject import W_Object
from rupypy.objects.stringobject import W_StringObject


def create_pack_table():
    ruby_fmt = "CcSsIiLlQqNnVvDdFfEeGgAaZ"
    py_fmt  = []
    py_fmt += "BbHhIiLlQq"
    py_fmt += [">H", ">I", "<H", "<I"]
    py_fmt += "ddff"
    py_fmt += ["<d", "<f", ">d", ">f"]
    py_fmt += "sss"
    table = [None] * (ord('z') - ord('A'))
    for c in ruby_fmt:
        table[ord(c) - ord('A')] = py_fmt[ruby_fmt.index(c)]
    return table
pack_table = create_pack_table()
fixnum_formats = "CcSsIiLlQqNnVvUw"
float_formats  = "DdFfEeGg"
string_formats = "AaBbHhMmPpuZ"


class W_ArrayObject(W_Object):
    classdef = ClassDef("Array", W_Object.classdef)
    classdef.include_module(Enumerable)

    def __init__(self, space, items_w):
        W_Object.__init__(self, space)
        self.items_w = items_w

    def listview(self, space):
        return self.items_w

    classdef.app_method("""
    def to_s()
        result = "["
        self.each_with_index do |obj, i|
            if i > 0
                result << ", "
            end
            result << obj.to_s
        end
        result << "]"
    end
    """)

    @classdef.method("at")
    @classdef.method("[]")
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
            self.items_w[start:end] = [w_obj]
        else:
            self.items_w[start] = w_obj
        return w_obj

    @classdef.method("size")
    @classdef.method("length")
    def method_length(self, space):
        return space.newint(len(self.items_w))

    @classdef.method("empty?")
    def method_emptyp(self, space):
        return space.newbool(len(self.items_w) == 0)

    @classdef.method("+")
    def method_add(self, space, w_other):
        assert isinstance(w_other, W_ArrayObject)
        return space.newarray(self.items_w + w_other.items_w)

    classdef.app_method("""
    def -(other)
        res = []
        self.each do |x|
            if !other.include?(x)
                res << x
            end
        end
        res
    end
    """)

    @classdef.method("<<")
    def method_lshift(self, space, w_obj):
        self.items_w.append(w_obj)
        return self

    @classdef.method("concat")
    def method_concat(self, space, w_ary):
        self.items_w += space.listview(w_ary)
        return self

    @classdef.method("push")
    def method_push(self, space, args_w):
        self.items_w.extend(args_w)
        return self

    @classdef.method("shift")
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

    @classdef.method("dup")
    def method_dup(self, space):
        return space.newarray(self.items_w[:])

    classdef.app_method("""
    def at idx
        self[idx]
    end
    """)

    classdef.app_method("""
    def each
        i = 0
        while i < self.length
            yield self[i]
            i += 1
        end
    end
    """)

    classdef.app_method("""
    def zip ary
        result = []
        self.each_with_index do |obj, idx|
            result << [obj, ary[idx]]
        end
        result
    end
    """)

    classdef.app_method("""
    def product ary
        result = []
        self.each do |obj|
            ary.each do |other|
                result << [obj, other]
            end
        end
        result
    end
    """)

    classdef.app_method("""
    def compact
        self.select { |each| !each.nil? }
    end
    """)

    classdef.app_method("""
    def reject!(&block)
        prev_size = self.size
        self.delete_if(&block)
        return nil if prev_size == self.size
        self
    end
    """)

    classdef.app_method("""
    def delete_if
        i = 0
        c = 0
        sz = self.size
        while i < sz - c
            item = self[i + c]
            if yield(item)
                c += 1
            else
                self[i] = item
                i += 1
            end
        end
        self.pop(c)
        self
    end
    """)

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
    def method_delete_at(self, space, idx):
        if idx >= len(self.items_w):
            return space.w_nil
        else:
            return self.items_w.pop(idx)

    @classdef.method("last")
    def method_last(self, space):
        if len(self.items_w) == 0:
            return space.w_nil
        else:
            return self.items_w[len(self.items_w) - 1]

    @classdef.method("pack", template="str")
    def method_pack(self, space, template):
        result = []
        idx = 0
        iidx = 0

        while idx < len(template):
            ch = template[idx]

            endianess = "@"
            if ch in "SsIiLlQq":
                # These allow other endianess definitions
                if idx + 1 < len(template):
                    ch2 = template[idx + 1]
                    if ch2 == "!" and idx + 2 < len(template) and template[idx + 2] in "<>":
                        endianess = template[idx + 2]
                        idx += 2
                    elif ch2 in "<>":
                        idx += 1
                        endianess = ch2
                    elif ch2 in "!_":
                        idx += 1
            elif ch == "Z":
                if idx + 1 < len(template) and template[idx + 1] == "*":
                    # star adds \0, defer to the next iteration
                    template[idx + 1] = "x"

            count_digits = 0
            while idx + count_digits + 1 < len(template):
                if template[idx + count_digits + 1].isdigit():
                    count_digits += 1
                else:
                    break
            idx += 1
            if count_digits > 0:
                count = int(template[idx:idx + count_digits])
                idx += count_digits
            else:
                count = 1

            fmt_point = ord(ch) - ord('A')
            if fmt_point < 0 or fmt_point > len(pack_table) or pack_table[fmt_point] is None:
                # Anything now does not advance in the data
                if ch == "@":
                    if len(result) < count:
                        result += ["\0"] * (count - len(result))
                    else:
                        result = result[:count]
                elif ch == "X":
                    if not result:
                        raise space.error(space.w_ArgumentError, "X outside of string")
                    else:
                        result.pop()
                elif ch == "x":
                    result += ["\0"] * count
            elif ch in string_formats:
                if ch in "BbHhMmPpu":
                    raise NotImplementedError("%s in string packing" % ch)

                fmt = "%d%s" % (count, pack_table[ord(ch) - ord('A')])
                string = space.str_w(space.convert_type(
                        self.items_w[iidx], space.getclassfor(W_StringObject), "to_str"
                ))
                if ch == "A":
                    string = string[:count]
                    result += struct.pack("%ds" % len(string), string).ljust(count)
                else:
                    result += struct.pack(fmt, string)
                iidx += 1
            else:
                if iidx + count > len(self.items_w):
                    raise space.error(space.w_ArgumentError, "too few arguments")
                fmt = "%s%s" % (endianess, pack_table[ord(ch) - ord('A')])

                if ch in fixnum_formats:
                    if ch in "Uw":
                        raise NotImplementedError("UTF-8 and BER pack")

                    for i in range(count):
                        num = space.int_w(
                            space.convert_type(self.items_w[iidx + i], space.w_fixnum, "to_int")
                        )
                        result += struct.pack(fmt, num)
                elif ch in float_formats:
                    for i in range(count):
                        w_item = self.items_w[iidx + 1]
                        if not isinstance(w_item, W_FloatObject):
                            raise space.error(
                                space.w_TypeError,
                                "can't convert %s into Float" % space.getclass(w_item).name
                            )
                        flt = space.float_w(w_item)
                        result += struct.pack(fmt, flt)
                iidx += count

        return space.newstr_fromchars(result)
