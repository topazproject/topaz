from pypy.rlib.rarithmetic import ovfcheck
from pypy.rlib.rstruct.nativefmttable import native_is_bigendian
from pypy.rlib.unroll import unrolling_iterable


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
    def __init__(self, fmt):
        self.fmt = fmt

    def native_code_count(self, space, fmt, idx):
        end = idx + 1
        while end < len(fmt) and fmt[end] in native_endian_codes:
            end += 1
        native_chars = end - idx - 1
        if native_chars > 0 and ch not in native_codes:
            raise space.error(
                space.w_ArgumentError,
                "%s allowed only after types %s" % (modifier, native_codes)
            )
        return native_chars

    def check_for_bigendianess_code(self, space, fmt, idx):
        end = idx + 1
        while end < len(fmt) and fmt[end] in endianess_codes:
            end += 1
        endian_chars = end - idx - 1
        if endian_chars > 0 and ch not in mappable_codes:
            raise space.error(
                space.w_ArgumentError,
                "%s allowed only after types %s" % (modifier, native_codes)
            )
        elif endian_chars > 1:
            raise space.error(space.w_RangeError, "Can't use both '<' and '>'")
        elif endian_chars == 1:
            bigendian = (fmt[end - 1] == BE_modifier)
        else:
            bigendian = native_is_bigendian
        return bigendian

    def check_for_star(self, space, fmt, idx):
        return idx + 1 < len(fmt) and fmt[idx] in starrable_codes and fmt[idx + 1] == "*"

    def determine_repetitions(self, space, fmt, idx):
        end = idx + 1
        if end < len(fmt) and fmt[end].isdigit():
            repetitions = ord(fmt[end]) - ord('0')
            end += 1
            while end < len(fmt) and fmt[end].isdigit():
                try:
                    repetitions = ovfcheck(repetitions * 10 + (ord(fmt[end]) - ord('0')))
                except OverflowError:
                    raise space.error(space.w_RangeError, "pack length too big")
                end += 1
        else:
            repetitions = 1
        return (repetitions, end - 1)

    def interpret(self, space, fmt):
        result = []
        idx = 0

        while idx < len(fmt):
            ch = fmt[idx]

            # Skip any garbage
            if ch not in codes:
                idx += 1
                continue

            native_code_count = self.native_code_count(space, fmt, idx)
            idx += native_code_count

            bigendian = self.check_for_bigendianess_code(space, fmt, idx)
            if bigendian:
                idx += 1

            starred = self.check_for_star(space, fmt, idx)
            if starred:
                idx += 1

            repetitions, idx = self.determine_repetitions(space, fmt, idx)

            converter_idx = ord(ch)
            if starred:
                converter_idx -= 1

            if bigendian != native_is_bigendian:
                converter_idx += non_native_endianess_offset

            result.append([converter_idx, repetitions])
            idx += 1
        return result

    def operate(self, space, fmt, code=None, args_w=[]):
        converter_indices = self.interpret(space, fmt)
        result = []
        if code:
            for idx, reps in converter_indices:
                result.extend(unpack_operators[idx](space, code, reps))
        elif args_w:
            for idx, reps in converter_indices:
                result.extend(pack_operators[idx](space, args_w, reps))
        return result

    def pack(self, space, args_w):
        return space.newstr_fromchars(self.operate(space, self.fmt, args_w=args_w))

    def unpack(self, space, code):
        return space.newarray(self.operate(space, self.fmt, code=code))


# class Operator(object):
#     def __init__(self, repetitions):
#         self.repetitions = repetitions

#     def pack(space, args_w):
#         pass

#     def unpack(space, code):
#         pass


# class IntOperator(Operator):
#     def __init__(self, repetitions)

#     def pack(space, args_w):
#         result = []
#         if self.repetitions > len(args_w):
#             raise space.error(space.w_ArgumentError, "too few arguments")
#         for i in range(self.repetitions):
#             num = space.int_w(
#                 space.convert_type(args_w[i], space.w_fixnum, "to_int")
#             )
#             result += struct.pack(fmt, num)
#         return result


# class FloatOperator(Operator):
#     def __init__(self, fmt):
#         self.fmt = fmt

#     def encode(space, args_w, count=count):
#         result = []
#         if count > len(args_w):
#             raise space.error(space.w_ArgumentError, "too few arguments")
#         for i in range(count):
#             w_item = args_w[iidx + 1]
#             if not isinstance(w_item, W_FloatObject):
#                 raise space.error(
#                     space.w_TypeError,
#                     "can't convert %s into Float" % space.getclass(w_item).name
#                 )
#             result += struct.pack(fmt, space.float_w(w_item))
#         return result


def make_int_packer(size=0, signed=True):
    def pack_int(space, args_w, repetitions):
        if repetitions > len(args_w):
            raise space.error(space.w_ArgumentError, "too few arguments")

        unroll_revrange_size = unrolling_iterable(range(size - 1, -1, -1))
        result = []
        for i in range(repetitions):
            num = space.int_w(
                space.convert_type(args_w[i], space.w_fixnum, "to_int")
            )
            if native_is_bigendian:
                for i in unroll_revrange_size:
                    x = (num >> (8*i)) & 0xff
                    result.append(chr(x))
            else:
                for i in unroll_revrange_size:
                    result.append(chr(num & 0xff))
                    num >>= 8
        return result
    return pack_int


pack_operators = [None] * 255
pack_operators[ord('C')] = make_int_packer(size=1, signed=False)
# converters[ord('c')] = IntMappingConverter("b", min=-2**7, max=2**7 - 1)
# converters[ord('S')] = IntMappingConverter("H", min=0, max=2**16)
# converters[ord('s')] = IntMappingConverter("h", min=-2**15, max=2**15 - 1)

# tmp = IntMappingConverter("I", min=0, max=2**32)
# converters[ord('I')] = tmp
# converters[ord('L')] = tmp

# tmp = IntMappingConverter("i", min=-2**31, max=2**31 - 1)
# converters[ord('i')] = tmp
# converters[ord('l')] = tmp

# converters[ord('Q')] = IntMappingConverter("Q", min=0, max=2**64)
# converters[ord('q')] = IntMappingConverter("q", min=-2**63, max=2**63 - 1)

# converters[ord('s') + BE_offset] = IntMappingConverter(">h", min=-2**15, max=2**15 - 1)
# converters[ord('s') + LE_offset] = IntMappingConverter("<h", min=-2**15, max=2**15 - 1)

# tmp = IntMappingConverter(">H", min=0, max=2**16)
# converters[ord('n')] = tmp
# converters[ord('S') + BE_offset] = tmp
# tmp = IntMappingConverter("<H", min=0, max=2**16)
# converters[ord('v')] = tmp
# converters[ord('S') + LE_offset] = tmp

# tmp = IntMappingConverter(">I", min=0, max=2**32)
# converters[ord('N')] = tmp
# converters[ord('I') + BE_offset] = tmp
# converters[ord('L') + BE_offset] = tmp
# tmp = IntMappingConverter("<I", min=0, max=2**32)
# converters[ord('V')] = tmp
# converters[ord('i') + LE_offset] = tmp
# converters[ord('l') + LE_offset] = tmp

# converters[ord('Q') + BE_offset] = IntMappingConverter(">Q", min=0, max=2**64)
# converters[ord('Q') + LE_offset] = IntMappingConverter("<Q", min=0, max=2**64)
# converters[ord('q') + BE_offset] = IntMappingConverter(">q", min=-2**63, max=2**63 - 1)
# converters[ord('q') + LE_offset] = IntMappingConverter("<q", min=-2**63, max=2**63 - 1)

# converters[ord('U')] = IntMappingConverter("i", min=-2**31, max=2**31 - 1)
# converters[ord('w')] = IntMappingConverter("i", min=-2**31, max=2**31 - 1)

# converters[ord('f')] = converters[ord('F')] = FloatMappingConverter("f")
# converters[ord('d')] = converters[ord('D')] = FloatMappingConverter("d")
# converters[ord('E')] = FloatMappingConverter("<d")
# converters[ord('e')] = FloatMappingConverter("<f")
# converters[ord('G')] = FloatMappingConverter(">d")
# converters[ord('g')] = FloatMappingConverter(">f")

# converters[ord('A')] = StringMappingConverter("s", padding=" ")
# converters[ord('a')] = StringMappingConverter("s")
# converters[ord('Z')] = StringMappingConverter("s")
# converters[ord('Z') - 1] = StringMappingConverter("Z", end_null=True)

# converters[ord('B')] = BitStringConverter(msb=True)
# converters[ord('b')] = BitStringConverter(msb=False)
# converters[ord('H')] = HexStringConverter(high=True)
# converters[ord('h')] = HexStringConverter(high=False)
# converters[ord('u')] = UUStringConverter()
# converters[ord('M')] = QuotedPrintableStringConverter()
# converters[ord('m')] = Base64StringConverter()
# converters[ord('P')] # not supported
# converters[ord('p')] # not supported

# converters[ord('@')] = MoveTo()
# converters[ord('X')] = BackUp()
# converters[ord('x')] = Padding()
