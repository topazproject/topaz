from rpython.rlib import jit
from rpython.rlib.rfloat import formatd
from rpython.rlib.unroll import unrolling_iterable

from topaz.coerce import Coerce

FORMAT_CHARS = unrolling_iterable([
    ((c, c) if type(c) is str else c) for c in [
        "s", "d", "f", ("%", "percent"), ("\0", "percent"), ("\n", "percent"),
    ]
])


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
                if self.fmt[i] == "%":
                    break
                i += 1
            else:
                result_w.append(space.newstr_fromstr(self.fmt[start:i]))
                break
            result_w.append(space.newstr_fromstr(self.fmt[start:i]))
            i += 1
            if i >= len(self.fmt):
                result_w.append(self.fmt_percent(space, 0, " "))
                return result_w
            width = 0
            while self.fmt[i].isdigit():
                width = width * 10 + (ord(self.fmt[i]) - ord("0"))
                i += 1
            format_char = self.fmt[i]
            i += 1
            for c, postfix in FORMAT_CHARS:
                if c == format_char:
                    try:
                        w_res = getattr(self, "fmt_" + postfix)(space, width, format_char)
                    except IndexError:
                        raise space.error(
                            space.w_ArgumentError,
                            "too many format specifiers"
                        )
                    result_w.append(w_res)
                    break
            else:
                raise space.error(space.w_NotImplementedError, "%%%s" % format_char)
        return result_w

    def _next_item(self):
        w_item = self.items_w[self.item_index]
        self.item_index += 1
        return w_item

    def _fmt_num(self, space, num, width):
        return space.newstr_fromstr((width - len(num)) * "0" + num)

    def fmt_s(self, space, width, format_char):
        return space.send(self._next_item(), "to_s")

    def fmt_d(self, space, width, format_char):
        num = Coerce.int(space, self._next_item())
        return self._fmt_num(space, str(num), width)

    def fmt_f(self, space, width, format_char):
        num = Coerce.float(space, self._next_item())
        return self._fmt_num(space, formatd(num, "f", 6), width)

    def fmt_percent(self, space, width, format_char):
        if format_char in "\0\n":
            return space.newstr_fromchars(["%", format_char])
        else:
            return space.newstr_fromstr("%")
