from __future__ import absolute_import
from topaz.module import ModuleDef
from topaz.objects.arrayobject import W_ArrayObject
from topaz.objects.boolobject import W_TrueObject, W_FalseObject
from topaz.objects.intobject import W_FixnumObject
from topaz.objects.hashobject import W_HashObject
from topaz.objects.nilobject import W_NilObject
from topaz.objects.stringobject import W_StringObject
from topaz.objects.symbolobject import W_SymbolObject
from topaz.objects.ioobject import W_IOObject
from topaz.objects.floatobject import W_FloatObject

import os
import math


class Marshal(object):
    moduledef = ModuleDef("Marshal")

    MAJOR_VERSION = 4
    MINOR_VERSION = 8

    NIL = 0x30
    TRUE = 0x54
    FALSE = 0x46
    FIXNUM = 0x69
    ARRAY = 0x5b
    SYMBOL = 0x3a
    IVAR = 0x49
    STRING = 0x22
    HASH = 0x7b
    FLOAT = 0x66

    @moduledef.setup_module
    def setup_module(space, w_mod):
        space.set_const(w_mod, "MAJOR_VERSION", space.newint(Marshal.MAJOR_VERSION))
        space.set_const(w_mod, "MINOR_VERSION", space.newint(Marshal.MINOR_VERSION))

    @staticmethod
    def dump(space, w_obj):
        bytes = []
        if isinstance(w_obj, W_NilObject):
            bytes.append(Marshal.NIL)
        elif isinstance(w_obj, W_TrueObject):
            bytes.append(Marshal.TRUE)
        elif isinstance(w_obj, W_FalseObject):
            bytes.append(Marshal.FALSE)
        elif isinstance(w_obj, W_FixnumObject):
            bytes.append(Marshal.FIXNUM)
            bytes += Marshal.integer2bytes(space.int_w(w_obj))
        elif isinstance(w_obj, W_FloatObject):
            bytes.append(Marshal.FLOAT)
            raw_value = space.float_w(w_obj)
            int_value = int(raw_value)
            float_value = raw_value
            string = ""  # None

            if raw_value == int_value:
                float_value = int_value
                # repr would be more accurate here, but it weirdly does not translate
                if str(raw_value) == "-0.0":  # slowing things down
                    string = "-0"
                else:
                    string = str(float_value)
            else:  # encode float
                string = str(float_value)

            length = len(string)
            bytes += Marshal.integer2bytes(length)
            for c in string:
                bytes.append(ord(c))
        elif isinstance(w_obj, W_ArrayObject):
            array = space.listview(w_obj)
            bytes.append(Marshal.ARRAY)
            bytes += Marshal.integer2bytes(len(array))
            for item in array:
                bytes += Marshal.dump(space, item)
        elif isinstance(w_obj, W_SymbolObject):
            bytes.append(Marshal.SYMBOL)
            symbol = space.symbol_w(w_obj)
            bytes += Marshal.integer2bytes(len(symbol))
            for char in symbol:
                bytes.append(ord(char))
        elif isinstance(w_obj, W_StringObject):
            string = space.str_w(w_obj)
            bytes.append(Marshal.IVAR)
            bytes.append(Marshal.STRING)
            bytes += Marshal.integer2bytes(len(string))
            for char in string:
                bytes.append(ord(char))
            bytes.append(0x06)
            # TODO: respect encoding
            bytes += Marshal.dump(space, space.newsymbol("E"))
            bytes += Marshal.dump(space, space.w_true)
        elif isinstance(w_obj, W_HashObject):
            bytes.append(Marshal.HASH)
            hash_len = w_obj.strategy.len(w_obj.dict_storage)
            hash_keys_w = w_obj.strategy.keys(w_obj.dict_storage)
            bytes += Marshal.integer2bytes(hash_len)
            for w_key in hash_keys_w:
                bytes += Marshal.dump(space, w_key)
                w_value = w_obj.strategy.getitem(w_obj.dict_storage, w_key)
                bytes += Marshal.dump(space, w_value)
        else:
            raise NotImplementedError(type(w_obj))

        return bytes

    @staticmethod
    def load(space, bytes, offset=0):
        byte = bytes[offset]
        if byte == Marshal.NIL:
            return space.w_nil, 1
        elif byte == Marshal.TRUE:
            return space.w_true, 1
        elif byte == Marshal.FALSE:
            return space.w_false, 1
        elif byte == Marshal.FIXNUM:
            value, length = Marshal.bytes2integer(bytes, offset + 1)
            return space.newint(value), length
        elif byte == Marshal.FLOAT:
            count, length = Marshal.bytes2integer(bytes, offset + 1)

            chars = []
            for i in range(length, length + count):
                chars.append(chr(bytes[offset + i]))

            return space.newfloat(float("".join(chars))), length
        elif byte == Marshal.ARRAY:
            count, skip = Marshal.bytes2integer(bytes, offset + 1)

            array = []
            for i in range(0, count):
                assert skip > 0
                element, l = Marshal.load(space, bytes, offset + skip)
                skip += l
                array.append(element)

            return space.newarray(array), skip
        elif byte == Marshal.SYMBOL:
            count, length = Marshal.bytes2integer(bytes, offset + 1)

            chars = []
            for i in range(length, length + count):
                chars.append(chr(bytes[offset + i]))

            return space.newsymbol("".join(chars)), length + count
        elif byte == Marshal.IVAR:
            # TODO: fully interpret IVARS
            if bytes[offset + 1] == Marshal.STRING:
                count, length = Marshal.bytes2integer(bytes, offset + 2)
                encoding = 6
                chars = []
                # TODO: take encoding into consideration
                for i in range(length + 1, length + count + 1):
                    chars.append(chr(bytes[offset + i]))
                return space.newstr_fromstr("".join(chars)), count + length + encoding
            else:
                raise NotImplementedError(bytes[offset + 1])
        elif byte == Marshal.HASH:
            count, skip = Marshal.bytes2integer(bytes, offset + 1)
            w_hash = space.newhash()
            for i in range(0, count):
                assert skip > 0
                k, s = Marshal.load(space, bytes, offset + skip)
                skip += s
                assert skip > 0
                v, s = Marshal.load(space, bytes, offset + skip)
                skip += s
                w_hash.method_subscript_assign(space, k, v)
            return w_hash, skip
        else:
            raise NotImplementedError(byte)

    @moduledef.function("dump")
    def method_dump(self, space, w_obj, w_io=None):
        bytes = [4, 8]
        bytes += Marshal.dump(space, w_obj)
        string = "".join([chr(byte) for byte in bytes])

        if w_io is not None:
            assert isinstance(w_io, W_IOObject)
            w_io.ensure_not_closed(space)
            os.write(w_io.fd, string)
            return w_io
        else:
            return space.newstr_fromstr(string)

    @moduledef.function("load")
    @moduledef.function("restore")
    def method_load(self, space, w_obj):
        string = ""

        if isinstance(w_obj, W_IOObject):
            w_obj.ensure_not_closed(space)
            string = os.read(w_obj.fd, int(os.fstat(w_obj.fd).st_size))
        elif isinstance(w_obj, W_StringObject):
            string = space.str_w(w_obj)
        else:
            raise space.error(space.w_TypeError, "instance of IO needed")

        if len(string) < 2:
            raise space.error(space.w_ArgumentError, "marshal data too short")

        bytes = [ord(string[i]) for i in range(0, len(string))]
        if int(bytes[0]) != Marshal.MAJOR_VERSION or int(bytes[1]) != Marshal.MINOR_VERSION:
            raise space.error(
                space.w_TypeError,
                "incompatible marshal file format (can't be read)\n"
                "format version %s.%s required; %s.%s given"
                % (Marshal.MAJOR_VERSION, Marshal.MINOR_VERSION, bytes[0], bytes[1])
            )

        return Marshal.load(space, bytes, 2)[0]

    # extract integer from marshalled byte array
    # least significant byte first
    @staticmethod
    def bytes2integer(bytes, offset):
        if bytes[offset] >= 252:
            value = 256 - bytes[offset + 1]
            for i in range(2, 256 - bytes[offset] + 1):
                value += (255 - bytes[offset + i]) * int(math.pow(256, i - 1))
            return -value, 256 - bytes[offset] + 2
        elif bytes[offset] > 0 and bytes[offset] < 6:
            value = bytes[offset + 1]
            for i in range(2, bytes[offset] + 1):
                value += bytes[offset + i] * int(math.pow(256, i - 1))
            return value, bytes[offset] + 2
        else:
            value = bytes[offset]
            if value == 0:
                return 0, 2
            elif value > 127:
                return value - 251, 2
            else:
                return value - 5, 2

    # least significant byte first
    @staticmethod
    def integer2bytes(value):
        bytes = []

        if value > 2 ** 30 - 1:
            raise NotImplementedError("Bignum")

        if value > 2 ** 24 - 1:
            bytes.append(4)
            bytes.append(value % 256)
            bytes.append((value >> 8) % 256)
            bytes.append((value >> 16) % 256)
            bytes.append((value >> 24) % 256)
        elif value > 2 ** 16 - 1:
            bytes.append(3)
            bytes.append(value % 256)
            bytes.append((value >> 8) % 256)
            bytes.append((value >> 16) % 256)
        elif value > 255:
            bytes.append(2)
            bytes.append(value % 256)
            bytes.append((value >> 8) % 256)
        elif value > 122:
            bytes.append(1)
            bytes.append(value)
        elif value > 0:
            bytes.append(value + 5)
        elif value == 0:
            bytes.append(0)
        elif value > -124:
            bytes.append(251 + value)
        elif value > -257:
            bytes.append(0xff)
            bytes.append(256 + value)
        elif value > -(2 ** 16 + 1):
            bytes.append(0xfe)
            bytes.append(value % 256)
            bytes.append((value >> 8) % 256)
        elif value > -(2 ** 24 + 1):
            bytes.append(0xfd)
            bytes.append(value % 256)
            bytes.append((value >> 8) % 256)
            bytes.append((value >> 16) % 256)
        elif value > -(2 ** 30 + 1):
            bytes.append(0xfc)
            bytes.append(value % 256)
            bytes.append((value >> 8) % 256)
            bytes.append((value >> 16) % 256)
            bytes.append((value >> 24) % 256)
        else:
            raise NotImplementedError("number too small")
        return bytes
