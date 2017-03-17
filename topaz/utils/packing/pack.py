from rpython.rlib import jit
from rpython.rlib.rarithmetic import ovfcheck
from rpython.rlib.rstruct.nativefmttable import native_is_bigendian

from topaz.utils.packing.floatpacking import make_float_packer
from topaz.utils.packing.intpacking import make_int_packer
from topaz.utils.packing.stringpacking import make_string_packer, pack_pointer


codes = "CcSsIiLlQqNnVvUwDdFfEeGgAaZBbHhuMmPp@Xx"
mappable_codes = "SsIiLlQq"
native_codes = "SsIiLl"
starrable_codes = "Z"
endianess_codes = "<>"
native_endian_codes = "!_"
moving_chars = "@Xx"

BE_modifier = ">"
LE_offset = ord("<") if native_is_bigendian else 0
BE_offset = 0 if native_is_bigendian else ord(">")
non_native_endianess_offset = LE_offset if native_is_bigendian else BE_offset


class RPacker(object):
    def __init__(self, fmt, args_w):
        self.fmt = fmt
        self.args_w = args_w
        self.args_index = 0
        self.result = []

    def native_code_count(self, space, idx, ch):
        end = idx + 1
        while end < len(self.fmt) and self.fmt[end] in native_endian_codes:
            end += 1
        native_chars = end - idx - 1
        if native_chars > 0 and ch not in native_codes:
            raise space.error(space.w_ArgumentError,
                "%s allowed only after types %s" % (self.fmt[idx + 1], native_codes)
            )
        return native_chars

    def check_for_bigendianess_code(self, space, idx, ch):
        end = idx + 1
        while end < len(self.fmt) and self.fmt[end] in endianess_codes:
            end += 1
        endian_chars = end - idx - 1
        if endian_chars > 0 and ch not in mappable_codes:
            raise space.error(space.w_ArgumentError,
                "%s allowed only after types %s" % (self.fmt[idx + 1], mappable_codes)
            )
        elif endian_chars > 1:
            raise space.error(space.w_RangeError, "Can't use both '<' and '>'")
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

    def determine_repetitions(self, space, idx):
        end = idx + 1
        repetitions = 0
        while end < len(self.fmt) and self.fmt[end].isdigit():
            try:
                repetitions = ovfcheck(repetitions * 10 + (ord(self.fmt[end]) - ord("0")))
            except OverflowError:
                raise space.error(space.w_RangeError, "pack length too big")
            end += 1
        if end == idx + 1:
            # No explicit repetitions definition
            repetitions = 1
        return (repetitions, end - 1)

    @jit.unroll_safe
    def interpret(self, space):
        idx = 0
        indices = []

        while idx < len(self.fmt):
            ch = self.fmt[idx]

            # Skip any garbage
            if ch not in codes:
                idx += 1
                continue

            native_code_count = self.native_code_count(space, idx, ch)
            idx += native_code_count

            bigendian = self.check_for_bigendianess_code(space, idx, ch)
            if bigendian:
                idx += 1

            starred = self.check_for_star(idx, ch)
            if starred:
                idx += 1

            repetitions, idx = self.determine_repetitions(space, idx)

            converter_idx = ord(ch)
            if starred:
                converter_idx -= 1

            if bigendian != native_is_bigendian:
                converter_idx += non_native_endianess_offset

            indices.append((converter_idx, repetitions))
            idx += 1
        return indices

    @jit.look_inside_iff(lambda self, space: jit.isconstant(self.fmt))
    def operate(self, space):
        indices = self.interpret(space)
        for idx, reps in indices:
            op = pack_operators[idx]
            if op is None:
                raise space.error(space.w_NotImplementedError, "Operator %s" % chr(idx))
            op(space, self, reps)
        return self.result


def pack_move_to(space, packer, position):
    if len(packer.result) < position:
        packer.result.extend(["\0"] * (position - len(packer.result)))
    else:
        assert position >= 0
        del packer.result[position:]


def pack_back_up(space, packer, repetitions):
    size = len(packer.result)
    if size < repetitions:
        raise space.error(space.w_ArgumentError, "X outside of string")
    else:
        begin = size - repetitions
        assert begin >= 0
        del packer.result[begin:]


def pack_padding(space, packer, repetitions):
    packer.result.extend(["\0"] * repetitions)


def make_pack_operators():
    ops = [None] * 255

    # Int Basics
    int_sizes = "csiq"
    for size, code in enumerate(int_sizes):
        sidx = ord(code)
        uidx = ord(code.upper())
        ops[sidx] = make_int_packer(size=2 ** size, signed=True, bigendian=native_is_bigendian)
        ops[uidx] = make_int_packer(size=2 ** size, signed=False, bigendian=native_is_bigendian)
        if size > 0:
            ops[sidx + BE_offset] = make_int_packer(size=2 ** size, signed=True, bigendian=True)
            ops[uidx + BE_offset] = make_int_packer(size=2 ** size, signed=False, bigendian=True)
            ops[sidx + LE_offset] = make_int_packer(size=2 ** size, signed=True, bigendian=False)
            ops[uidx + LE_offset] = make_int_packer(size=2 ** size, signed=False, bigendian=False)
    # Int Aliases
    ops[ord("L")] = ops[ord("I")]
    ops[ord("L") + BE_offset] = ops[ord("N")] = ops[ord("I") + BE_offset]
    ops[ord("L") + LE_offset] = ops[ord("V")] = ops[ord("I") + LE_offset]
    ops[ord("l")] = ops[ord("i")]
    ops[ord("l") + BE_offset] = ops[ord("i") + BE_offset]
    ops[ord("l") + LE_offset] = ops[ord("i") + LE_offset]
    ops[ord("n")] = ops[ord("S") + BE_offset]
    ops[ord("v")] = ops[ord("S") + LE_offset]

    # ops[ord("U")] # pack UTF-8 sequence
    # ops[ord("w")] # BER-compressed integer

    ops[ord("f")] = ops[ord("F")] = make_float_packer(size=4, bigendian=native_is_bigendian)
    ops[ord("d")] = ops[ord("D")] = make_float_packer(size=8, bigendian=native_is_bigendian)
    ops[ord("E")] = make_float_packer(size=8, bigendian=False)
    ops[ord("e")] = make_float_packer(size=4, bigendian=False)
    ops[ord("G")] = make_float_packer(size=8, bigendian=True)
    ops[ord("g")] = make_float_packer(size=4, bigendian=True)

    ops[ord("A")] = make_string_packer(padding=" ")
    ops[ord("a")] = ops[ord("Z")] = make_string_packer(padding="\0")
    ops[ord("Z") - 1] = make_string_packer(nullterminated=True)

    # ops[ord("B")] # bitstring (msb first)
    # ops[ord("b")] # bitstring (lsb first)
    # ops[ord("H")] # hexstring (high first)
    # ops[ord("h")] # hexstring (low first)
    # ops[ord("u")] # UU-encoding
    # ops[ord("M")] # MIME-encoding
    # ops[ord("m")] # base64-encoding
    ops[ord("P")] = ops[ord("p")] = pack_pointer

    ops[ord("@")] = pack_move_to
    ops[ord("X")] = pack_back_up
    ops[ord("x")] = pack_padding

    return ops


pack_operators = make_pack_operators()
