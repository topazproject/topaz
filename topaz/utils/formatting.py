from rpython.rlib import jit
from rpython.rlib.rfloat import formatd
from rpython.rlib.unroll import unrolling_iterable


FORMAT_CHARS = unrolling_iterable([
    "s", "d", "f"
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
            width = 0
            while self.fmt[i].isdigit():
                width = width * 10 + (ord(self.fmt[i]) - ord("0"))
                i += 1
            format_char = self.fmt[i]
            w_item = self.items_w[self.item_index]
            self.item_index += 1
            i += 1
            for c in FORMAT_CHARS:
                if c == format_char:
                    w_res = getattr(self, "fmt_" + c)(space, w_item, width)
                    result_w.append(w_res)
                    break
            else:
                raise NotImplementedError(format_char)
        return result_w

    def _fmt_num(self, space, num, width):
        return space.newstr_fromstr((width - len(num)) * "0" + num)

    def fmt_s(self, space, w_item, width):
        return space.send(w_item, "to_s")

    def fmt_d(self, space, w_item, width):
        num = space.int_w(w_item)
        return self._fmt_num(space, str(num), width)

    def fmt_f(self, space, w_item, width):
        num = space.float_w(w_item)
        return self._fmt_num(space, formatd(num, "f", 6), width)
