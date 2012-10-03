import string
import struct


codes = "CcSsIiLlQqNnVvUwDdFfEeGgAaZBbHhuMmPp@Xx"
mappable_codes = "SsIiLlQq"
native_codes = "SsIiLl"
endianess_codes = "<>"
native_endian_codes = "!_"
moving_chars = "@Xx"
BE_modifier = 60
LE_modifier = 61

class Pack(object):
    def __init__(self, fmt):
        self.fmt = fmt

    def pack(self, space, args_w):
        result = []
        idx = 0

        while idx < len(self.fmt):
            ch = self.fmt[idx]
            if ch not in codes:
                idx += 1
                continue

            end = idx + 1

            while end < len(self.fmt) and self.fmt[end] in native_endian_codes:
                end += 1
            native_chars = end - idx - 1

            while end < len(self.fmt) and self.fmt[end] in endianess_codes:
                end += 1
            endian_chars = end - idx - 1

            if ch == "Z" and end < len(self.fmt) and self.fmt[end] == "*":
                end += 1
                has_star = True
            else:
                has_star = False

            while end < len(self.fmt) and self.fmt[end] in string.digits():
                end += 1
            digits = end - idx - 1

            # Skip all garbage
            while end < len(self.fmt) and self.fmt[end] not in codes:
                end += 1

            if native_chars > 0 and ch not in native_codes:
                raise space.error(
                    space.w_ArgumentError,
                    "%s allowed only after types %s" % (modifier, native_codes)
                )
            if endian_chars > 0 and ch not in mappable_codes:
                raise space.error(
                    space.w_ArgumentError,
                    "%s allowed only after types %s" % (modifier, native_codes)
                )
            if endian_chars > 1:
                raise space.error(space.w_RangeError, "Can't use both '<' and '>'")
            if digits > 0:
                count = int(self.fmt[end - digits:end])
            else:
                count = 0

            converter_idx = ord(ch)
            if has_star:
                converter_idx -= 1
            elif endian_chars == 1:
                if self.fmt[idx + native_chars + 1] == ">":
                    converter_idx += BE_modifier
                else:
                    converter_idx += LE_modifier

            result.extend(converters[converter_idx].encode(space, args_w, count=count))
            idx += 1


class Converter(object):
    pass


class IntMappingConverter(Converter):
    def __init__(self, fmt, min=0, max=0):
        self.fmt = fmt
        self.min = min
        self.max = max

    def encode(space, args_w, count=count):
        result = []
        if count > len(args_w):
            raise space.error(space.w_ArgumentError, "too few arguments")
        for i in range(count):
            num = space.int_w(
                space.convert_type(self.items_w[iidx + i], space.w_fixnum, "to_int")
            )
            result += struct.pack(fmt, num)
        return result


class FloatMappingConverter(Converter):
    def __init__(self, fmt):
        self.fmt = fmt

    def encode(space, args_w, count=count):
        result = []
        if count > len(args_w):
            raise space.error(space.w_ArgumentError, "too few arguments")
        for i in range(count):
            w_item = args_w[iidx + 1]
            if not isinstance(w_item, W_FloatObject):
                raise space.error(
                    space.w_TypeError,
                    "can't convert %s into Float" % space.getclass(w_item).name
                )
            result += struct.pack(fmt, space.float_w(w_item))
        return result


converters = [None] * 255
converters[ord('C')] = IntMappingConverter("B", min=0, max=2**8)
converters[ord('c')] = IntMappingConverter("b", min=-2**7, max=2**7 - 1)
converters[ord('S')] = IntMappingConverter("H", min=0, max=2**16)
converters[ord('s')] = IntMappingConverter("h", min=-2**15, max=2**15 - 1)

tmp = IntMappingConverter("I", min=0, max=2**32)
converters[ord('I')] = tmp
converters[ord('L')] = tmp

tmp = IntMappingConverter("i", min=-2**31, max=2**31 - 1)
converters[ord('i')] = tmp
converters[ord('l')] = tmp

converters[ord('Q')] = IntMappingConverter("Q", min=0, max=2**64)
converters[ord('q')] = IntMappingConverter("q", min=-2**63, max=2**63 - 1)

converters[ord('s') + BE_modifier] = IntMappingConverter(">h", min=-2**15, max=2**15 - 1)
converters[ord('s') + LE_modifier] = IntMappingConverter("<h", min=-2**15, max=2**15 - 1)

tmp = IntMappingConverter(">H", min=0, max=2**16)
converters[ord('n')] = tmp
converters[ord('S') + BE_modifier] = tmp
tmp = IntMappingConverter("<H", min=0, max=2**16)
converters[ord('v')] = tmp
converters[ord('S') + LE_modifier] = tmp

tmp = IntMappingConverter(">I", min=0, max=2**32)
converters[ord('N')] = tmp
converters[ord('I') + BE_modifier] = tmp
converters[ord('L') + BE_modifier] = tmp
tmp = IntMappingConverter("<I", min=0, max=2**32)
converters[ord('V')] = tmp
converters[ord('i') + LE_modifier] = tmp
converters[ord('l') + LE_modifier] = tmp

converters[ord('Q') + BE_modifier] = IntMappingConverter(">Q", min=0, max=2**64)
converters[ord('Q') + LE_modifier] = IntMappingConverter("<Q", min=0, max=2**64)
converters[ord('q') + BE_modifier] = IntMappingConverter(">q", min=-2**63, max=2**63 - 1)
converters[ord('q') + LE_modifier] = IntMappingConverter("<q", min=-2**63, max=2**63 - 1)

# converters[ord('U')] = IntMappingConverter("i", min=-2**31, max=2**31 - 1)
# converters[ord('w')] = IntMappingConverter("i", min=-2**31, max=2**31 - 1)

converters[ord('f')] = converters[ord('F')] = FloatMappingConverter("f")
converters[ord('d')] = converters[ord('D')] = FloatMappingConverter("d")
converters[ord('E')] = FloatMappingConverter("<d")
converters[ord('e')] = FloatMappingConverter("<f")
converters[ord('G')] = FloatMappingConverter(">d")
converters[ord('g')] = FloatMappingConverter(">f")

converters[ord('A')] = StringMappingConverter("s", padding=" ")
converters[ord('a')] = StringMappingConverter("s")
converters[ord('Z')] = StringMappingConverter("s")
converters[ord('Z') - 1] = StringMappingConverter("Z", end_null=True)

# converters[ord('B')] = BitStringConverter(msb=True)
# converters[ord('b')] = BitStringConverter(msb=False)
# converters[ord('H')] = HexStringConverter(high=True)
# converters[ord('h')] = HexStringConverter(high=False)
# converters[ord('u')] = UUStringConverter()
# converters[ord('M')] = QuotedPrintableStringConverter()
# converters[ord('m')] = Base64StringConverter()
# converters[ord('P')] # not supported
# converters[ord('p')] # not supported

converters[ord('@')] = MoveTo()
converters[ord('X')] = BackUp()
converters[ord('x')] = Padding()
