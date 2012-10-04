from pypy.rlib import jit, longlong2float
from pypy.rlib.rarithmetic import ovfcheck
from pypy.rlib.rstruct.nativefmttable import native_is_bigendian
from pypy.rlib.rstruct.ieee import float_pack

from rupypy.objects.intobject import W_FixnumObject
from rupypy.objects.floatobject import W_FloatObject


codes = "CcSsIiLlQqNnVvUwDdFfEeGgAaZBbHhuMmPp@Xx"
mappable_codes = "SsIiLlQq"
native_codes = "SsIiLl"
starrable_codes = "Z"
endianess_codes = "<>"
native_endian_codes = "!_"
moving_chars = "@Xx"

BE_modifier = ">"
LE_offset = ord("<") if native_is_bigendian else 0
BE_offset = ord(">") if native_is_bigendian else 0
non_native_endianess_offset = LE_offset if native_is_bigendian else BE_offset


class RPacker(object):
    def __init__(self, space, fmt, args_w):
        self.space = space
        self.fmt = fmt
        self.args_w = args_w
        self.args_index = 0
        self.result = []

    def native_code_count(self, idx, ch):
        end = idx + 1
        while end < len(self.fmt) and self.fmt[end] in native_endian_codes:
            end += 1
        native_chars = end - idx - 1
        if native_chars > 0 and ch not in native_codes:
            raise self.space.error(
                self.space.w_ArgumentError,
                "%s allowed only after types %s" % (self.fmt[idx + 1], native_codes)
            )
        return native_chars

    def check_for_bigendianess_code(self, idx, ch):
        end = idx + 1
        while end < len(self.fmt) and self.fmt[end] in endianess_codes:
            end += 1
        endian_chars = end - idx - 1
        if endian_chars > 0 and ch not in mappable_codes:
            raise self.space.error(
                self.space.w_ArgumentError,
                "%s allowed only after types %s" % (self.fmt[idx + 1], native_codes)
            )
        elif endian_chars > 1:
            raise self.space.error(self.space.w_RangeError, "Can't use both '<' and '>'")
        elif endian_chars == 1:
            bigendian = (self.fmt[end - 1] == BE_modifier)
        else:
            bigendian = native_is_bigendian
        return bigendian

    def check_for_star(self, idx, ch):
        return (
            idx + 1 < len(self.fmt) and
            ch in starrable_codes and
            self.fmt[idx + 1] == "*"
        )

    def determine_repetitions(self, idx):
        end = idx + 1
        if end < len(self.fmt) and self.fmt[end].isdigit():
            repetitions = ord(self.fmt[end]) - ord('0')
            end += 1
            while end < len(self.fmt) and self.fmt[end].isdigit():
                try:
                    repetitions = ovfcheck(repetitions * 10 + (ord(self.fmt[end]) - ord('0')))
                except OverflowError:
                    raise self.space.error(self.space.w_RangeError, "pack length too big")
                end += 1
        else:
            repetitions = 1
        return (repetitions, end - 1)

    def interpret(self):
        idx = 0
        indices = []

        while idx < len(self.fmt):
            ch = self.fmt[idx]

            # Skip any garbage
            if ch not in codes:
                idx += 1
                continue

            native_code_count = self.native_code_count(idx, ch)
            idx += native_code_count

            bigendian = self.check_for_bigendianess_code(idx, ch)
            if bigendian:
                idx += 1

            starred = self.check_for_star(idx, ch)
            if starred:
                idx += 1

            repetitions, idx = self.determine_repetitions(idx)

            converter_idx = ord(ch)
            if starred:
                converter_idx -= 1

            if bigendian != native_is_bigendian:
                converter_idx += non_native_endianess_offset

            indices.append([converter_idx, repetitions])
            idx += 1
        return indices

    def operate(self):
        indices = self.interpret()
        for idx, reps in indices:
            pack_operators[idx](self, reps)
        return self.result


def make_int_packer(size=0, signed=True, bigendian=native_is_bigendian):
    def pack_int(packer, repetitions):
        space = packer.space
        if repetitions > len(packer.args_w):
            raise space.error(space.w_ArgumentError, "too few arguments")

        for i in xrange(packer.args_index, repetitions + packer.args_index):
            num = space.int_w(
                space.convert_type(packer.args_w[i], space.w_fixnum, "to_int")
            )
            if bigendian:
                for i in xrange(size - 1, -1, -1):
                    x = (num >> (8*i)) & 0xff
                    packer.result.append(chr(x))
            else:
                for i in xrange(size - 1, -1, -1):
                    packer.result.append(chr(num & 0xff))
                    num >>= 8
        packer.args_index += repetitions
    return pack_int

def pack_move_to(packer, position):
    if len(packer.result) < position:
        packer.result.extend(["\0"] * (position - len(packer.result)))
    else:
        assert position >= 0
        packer.result[position:len(packer.result)] = []

def pack_back_up(packer, repetitions):
    size = len(packer.result)
    if size < repetitions:
        raise packer.space.error(packer.space.w_ArgumentError, "X outside of string")
    else:
        begin = size - repetitions
        assert begin >= 0
        packer.result[begin:size] = []

def pack_padding(packer, repetitions):
    packer.result.extend(["\0"] * repetitions)

def make_float_packer(size=0, bigendian=native_is_bigendian):
    def pack_float(packer, repetitions):
        space = packer.space
        if repetitions > len(packer.args_w):
            raise space.error(space.w_ArgumentError, "too few arguments")
        for i in xrange(packer.args_index, repetitions + packer.args_index):
            w_item = packer.args_w[i]
            if not (isinstance(w_item, W_FloatObject) or isinstance(w_item, W_FixnumObject)):
                raise space.error(
                    space.w_TypeError,
                    "can't convert %s into Float" % space.getclass(w_item).name
                )
            doubleval = space.float_w(w_item)
            l = ["\0"] * size
            unsigned = float_pack(doubleval, size)
            if bigendian:
                for i in xrange(size - 1, -1, -1):
                    l[i] = chr((unsigned >> (i * 8)) & 0xff)
            else:
                for i in xrange(size):
                    l[i] = chr((unsigned >> (i * 8)) & 0xff)
            packer.result.extend(l)
        packer.args_index += repetitions
    return pack_float

def pack_string_common(packer, width):
    space = packer.space
    string = space.str_w(
        space.convert_type(packer.args_w[packer.args_index], space.w_string, "to_str")
    )
    packer.args_index += 1
    return string

def pack_string_space_padded(packer, width):
    assert width >= 0
    string = pack_string_common(packer, width)[:width]
    packer.result += string
    packer.result.extend([" "] * (width - len(string)))

def pack_string_null_padded(packer, width):
    assert width >= 0
    string = pack_string_common(packer, width)[:width]
    packer.result += string
    packer.result.extend(["\0"] * (width - len(string)))

def pack_string_null_terminated(packer, width):
    packer.result += pack_string_common(packer, width)
    packer.result.append("\0")

def make_pack_operators():
    ops = [None] * 255

    # Int Basics
    int_sizes = "csiq"
    for size in xrange(0, len(int_sizes)):
        code = int_sizes[size]
        sidx = ord(code)
        uidx = ord(code.upper())
        ops[sidx] = make_int_packer(size=2**size, signed=True)
        ops[uidx] = make_int_packer(size=2**size, signed=False)
        if size > 0:
            ops[sidx + BE_offset] = make_int_packer(size=2**size, signed=True, bigendian=True)
            ops[uidx + BE_offset] = make_int_packer(size=2**size, signed=False, bigendian=True)
            ops[sidx + LE_offset] = make_int_packer(size=2**size, signed=True, bigendian=False)
            ops[uidx + LE_offset] = make_int_packer(size=2**size, signed=False, bigendian=False)
    # Int Aliases
    ops[ord("L")] = ops[ord("I")]
    ops[ord("L") + BE_offset] = ops[ord("N")] = ops[ord("I") + BE_offset]
    ops[ord("L") + LE_offset] = ops[ord("V")] = ops[ord("I") + LE_offset]
    ops[ord("l")] = ops[ord("i")]
    ops[ord("l") + BE_offset] = ops[ord("i") + BE_offset]
    ops[ord("l") + LE_offset] = ops[ord("i") + LE_offset]
    ops[ord("n")] = ops[ord("S") + BE_offset]
    ops[ord("v")] = ops[ord("S") + LE_offset]

    # ops[ord('U')] # pack UTF-8 sequence
    # ops[ord('w')] # BER-compressed integer

    ops[ord('f')] = ops[ord('F')] = make_float_packer(size=4)
    ops[ord('d')] = ops[ord('D')] = make_float_packer(size=8)
    ops[ord('E')] = make_float_packer(size=8, bigendian=False)
    ops[ord('e')] = make_float_packer(size=4, bigendian=False)
    ops[ord('G')] = make_float_packer(size=8, bigendian=True)
    ops[ord('g')] = make_float_packer(size=4, bigendian=True)

    ops[ord('A')] = pack_string_space_padded
    ops[ord('a')] = ops[ord('Z')] = pack_string_null_padded
    ops[ord('Z') - 1] = pack_string_null_terminated

    # ops[ord('B')] # bitstring (msb first)
    # ops[ord('b')] # bitstring (lsb first)
    # ops[ord('H')] # hexstring (high first)
    # ops[ord('h')] # hexstring (low first)
    # ops[ord('u')] # UU-encoding
    # ops[ord('M')] # MIME-encoding
    # ops[ord('m')] # base64-encoding
    # ops[ord('P')] # pointer to fixed-length structure
    # ops[ord('p')] # pointer to null-terminated string

    ops[ord('@')] = pack_move_to
    ops[ord('X')] = pack_back_up
    ops[ord('x')] = pack_padding

    return ops

pack_operators = make_pack_operators()
