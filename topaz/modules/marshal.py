# http://daeken.com/python-marshal-format

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
        #print "start byte:", bytes
        byte = bytes[0]
        if byte == 0x30:
            return space.w_nil
        elif byte == 0x54:
            return space.w_true
        elif byte == 0x46:
            return space.w_false
        elif byte == 0x69:  # Small Integers
            return space.newint(Marshal.bytes2integer(bytes[1:]))
        elif byte == 0x5b:  # Array
            count = Marshal.bytes2integer(bytes[1:])
            array = []

            # TODO: implement second return value which returns the remaining
            # items of the byte array, because items have a different length
            for i in range(0, count):
                array.append(Marshal.load(space, bytes[i + 2:]))

            return space.newarray(array)
        elif byte == 0x3a:
            count = Marshal.bytes2integer(bytes[1:])
            chars = []
            for i in range(2, count + 2):
                chars.append(chr(bytes[i]))
            return space.newsymbol("".join(chars))
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
    @staticmethod
    def bytes2integer(bytes):
        value = bytes[0]
        if value == 0:
            return 0
        elif value > 127:
            return value - 251
        else:
            return value - 5

    @staticmethod
    def integer2bytes(value):
        bytes = []
        # TODO: return control byte? like 0x69 for small integers
        if value < -123 or value > 122:
            raise NotImplementedError("multi-byte Fixnum")
        if value > 0:
            bytes.append(value + 5)
        elif value < 0:
            bytes.append(251 + value)
        else:
            bytes.append(0)
        return bytes
