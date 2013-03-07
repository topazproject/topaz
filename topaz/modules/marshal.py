# http://daeken.com/python-marshal-format
# would it be faster to use integer and shift? certainly yes

from __future__ import absolute_import
from topaz.module import Module, ModuleDef
from topaz.objects.arrayobject import W_ArrayObject
from topaz.objects.boolobject import W_TrueObject, W_FalseObject
from topaz.objects.intobject import W_FixnumObject
from topaz.objects.hashobject import W_HashObject
from topaz.objects.nilobject import W_NilObject
from topaz.objects.stringobject import W_StringObject
from topaz.objects.symbolobject import W_SymbolObject


class Marshal(Module):
    moduledef = ModuleDef("Marshal", filepath=__file__)

    @moduledef.setup_module
    def setup_module(space, w_mod):
        space.set_const(w_mod, "MAJOR_VERSION", space.newint(4))
        space.set_const(w_mod, "MINOR_VERSION", space.newint(8))

    @staticmethod
    def dump(space, w_obj):
        bytes = []
        if isinstance(w_obj, W_NilObject):
            bytes.append(0x30)
        elif isinstance(w_obj, W_TrueObject):
            bytes.append(0x54)
        elif isinstance(w_obj, W_FalseObject):
            bytes.append(0x46)
        elif isinstance(w_obj, W_FixnumObject):
            bytes.append(0x69)
            bytes += Marshal.integer2bytes(space.int_w(w_obj))
        elif isinstance(w_obj, W_ArrayObject):
            array = space.listview(w_obj)
            bytes.append(0x5b)
            bytes += Marshal.integer2bytes(len(array))
            for item in array:
                bytes += Marshal.dump(space, item)
        elif isinstance(w_obj, W_SymbolObject):
            bytes.append(0x3a)
            symbol = space.symbol_w(w_obj)
            bytes += Marshal.integer2bytes(len(symbol))
            for char in symbol:
                bytes.append(ord(char))
        elif isinstance(w_obj, W_StringObject):
            string = space.str_w(w_obj)
            bytes.append(0x49)
            bytes.append(0x22)
            bytes += Marshal.integer2bytes(len(string))
            for char in string:
                bytes.append(ord(char))
            bytes.append(0x06)
            # for now work with default encoding
            bytes += Marshal.dump(space, space.newsymbol("E"))
            bytes += Marshal.dump(space, space.w_true)
        elif isinstance(w_obj, W_HashObject):
            bytes.append(0x7b)
            bytes += Marshal.integer2bytes(len(w_obj.contents))
            for w_key in w_obj.contents.keys():
                bytes += Marshal.dump(space, w_key)
                bytes += Marshal.dump(space, w_obj.contents[w_key])
        else:
            raise NotImplementedError(type(w_obj))

        return bytes

    @staticmethod
    def load(space, bytes):
        byte = bytes[0]
        if byte == 0x30:
            return space.w_nil
        elif byte == 0x54:
            return space.w_true
        elif byte == 0x46:
            return space.w_false
        elif byte == 0x69:  # Integer
            return space.newint(Marshal.bytes2integer(bytes[1:]))
        elif byte == 0x5b:  # Array
            count = Marshal.bytes2integer(bytes[1:])
            array = []

            # TODO: implement second return value which returns the remaining
            # items of the byte array, because items have a different length
            for i in range(0, count):
                array.append(Marshal.load(space, bytes[i + 2:]))

            return space.newarray(array)
        elif byte == 0x3a:  # Symbol
            count = Marshal.bytes2integer(bytes[1:])
            chars = []
            # TODO: this only works for symbols shorter than 123 characters!
            for i in range(2, count + 2):
                chars.append(chr(bytes[i]))
            return space.newsymbol("".join(chars))
        elif byte == 0x49:  # IVAR
            if bytes[1] == 0x22:  # String
                count = Marshal.bytes2integer(bytes[2:])
                chars = []
                # TODO: this only works for symbols shorter than 123 characters!
                # TODO: take encoding into consideration
                for i in range(3, count + 3):
                    chars.append(chr(bytes[i]))
                return space.newstr_fromstr("".join(chars))
            else:
                raise NotImplementedError(bytes[1])
        elif byte == 0x7b:  # Hash
            count = Marshal.bytes2integer(bytes[1:])
            w_hash = space.newhash()
            # TODO: see array
            for i in range(2, 2 + count * 4, 4):
                k = Marshal.load(space, bytes[i:])
                v = Marshal.load(space, bytes[i + 2:])
                w_hash.method_subscript_assign(k, v)
            return w_hash
        else:
            raise NotImplementedError(byte)

    @moduledef.function("dump")
    def method_dump(self, space, w_obj):
        bytes = [4, 8]
        bytes += Marshal.dump(space, w_obj)
        string = "".join("%02X" % byte for byte in bytes)
        return space.newstr_fromstr(string)

    @moduledef.function("load")
    def method_load(self, space, w_obj):
        string = space.str_w(w_obj)
        bytes = [int(string[i:i + 2], 16) for i in range(0, len(string), 2)]
        #print "loading", string, bytes
        return Marshal.load(space, bytes[2:])

    # extract integer from marshalled byte array
    # least significant byte first!
    @staticmethod
    def bytes2integer(bytes):
        if bytes[0] > 0 and bytes[0] < 6:
            value = bytes[1]
            for i in range(2, bytes[0] + 1):
                value += bytes[i] * 256 ** (i - 1)
            return value
        else:
            value = bytes[0]
            if value == 0:
                return 0
            elif value > 127:
                return value - 251
            else:
                return value - 5

    # least significant byte first!
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
