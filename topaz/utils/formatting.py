from rpython.rlib import jit
from rpython.rlib.rfloat import formatd
from rpython.rlib.unroll import unrolling_iterable


FORMAT_CHARS = unrolling_iterable([
    "s", "d", "i", "f"
])

DEFAULT_PRECISION = 6

class StringFormatter(object):
    def __init__(self, fmt, items_w):
        self.fmt = fmt
        self.items_w = items_w
        self.item_index = 0

    @jit.look_inside_iff(lambda self, space: jit.isconstant(self.fmt))
    def format(self, space):
        i = 0
        result_w = []
        while True:
            start = i
            while i < len(self.fmt):
                if self.fmt[i] == "%" and len(self.fmt) > i + 1 and self.fmt[i + 1] not in "\0\n\r":
                    # '%' before end-of-string, \0, or newline is regular char
                    break
                i += 1
            else:
                result_w.append(space.newstr_fromstr(self.fmt[start:i]))
                break
            result_w.append(space.newstr_fromstr(self.fmt[start:i]))
            i += 1
            width = 0
            max_width = -1
            while i < len(self.fmt) and self.fmt[i].isdigit():
                width = width * 10 + (ord(self.fmt[i]) - ord("0"))
                i += 1
            if i < len(self.fmt) and self.fmt[i] == ".":
                i += 1
                max_width = 0
                while i < len(self.fmt) and self.fmt[i].isdigit():
                    max_width = max_width * 10 + (ord(self.fmt[i]) - ord("0"))
                    i += 1
            if i >= len(self.fmt):
                raise space.error(
                    space.w_ArgumentError,
                    "malformed format string - %*[0-9]"
                )
            format_char = self.fmt[i]
            if self.item_index >= len(self.items_w):
                raise space.error(
                    space.w_ArgumentError,
                    "wrong number of arguments (%d for %d)" % (len(self.items_w), self.item_index)
                )
            w_item = self.items_w[self.item_index]
            self.item_index += 1
            i += 1
            for c in FORMAT_CHARS:
                if c == format_char:
                    w_res = getattr(self, "fmt_" + c)(space, w_item, width, max_width)
                    result_w.append(w_res)
                    break
            else:
                raise space.error(space.w_NotImplementedError, format_char)
        return result_w

    def _fmt(self, space, string, padding, width, max_width):
        string = string[:max_width]
        return space.newstr_fromstr((width - len(string)) * padding + string)

    def fmt_s(self, space, w_item, width, max_width):
        if not space.is_kind_of(w_item, space.w_string):
            w_str = space.send(w_item, "to_s")
            if not space.is_kind_of(w_item, space.w_string):
                string = space.any_to_s(w_item)
            else:
                string = space.str_w(w_str)
        else:
            string = space.str_w(w_item)
        return self._fmt(space, string, " ", width, max_width)

    def coerce_integer(self, space, w_item):
        w_ary = space.convert_type(w_item, space.w_array, "to_ary", raise_error=False)
        if w_ary is space.w_nil:
            w_int = space.convert_type(w_item, space.w_numeric, "to_int", raise_error=False)
            if w_int is space.w_nil:
                return space.int_w(space.convert_type(w_item, space.w_numeric, "to_i"))
            else:
                return space.int_w(w_int)
        else:
            return space.int_w(space.listview(w_ary)[0])

    def fmt_d(self, space, w_item, width, max_width):
        num = self.coerce_integer(space, w_item)
        return self._fmt(space, str(num), "0", width, max_width)

    fmt_i = fmt_d

    def fmt_f(self, space, w_item, width, max_width):
        if space.is_kind_of(w_item, space.w_float):
            num = space.float_w(w_item)
        else:
            num = space.float_w(space.send(space.w_object, "Float", [w_item]))
        return self._fmt(space, formatd(num, "f", 6), "0", width, max_width)
