from topaz.objects.objectobject import W_Object
from topaz.coerce import Coerce
from topaz.error import RubyError
from topaz.module import ClassDef
from rpython.rlib.rbigint import rbigint
from rpython.rtyper.lltypesystem import rffi

class W_BufferObject(W_Object):
    classdef = ClassDef('Buffer', W_Object.classdef)

    typesymbols = {'char': rffi.CHAR,
                   'uchar': rffi.CHAR,
                   'short': rffi.SHORT,
                   'ushort': rffi.SHORT,
                   'int': rffi.INT,
                   'uint': rffi.INT,
                   'long': rffi.LONG,
                   'ulong': rffi.ULONG,
                   'long_long': rffi.LONGLONG,
                   'ulong_long': rffi.ULONGLONG,
                   'float': rffi.FLOAT,
                   'double': rffi.DOUBLE}

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        pass
        # TODO: Try this, once method_alias works in topaz
        #w_cls.method_alias(space, space.newsymbol('alloc_inout'),
        #                          space.newsymbol('new'))
        # Repeat with all other aliases!

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_BufferObject(space)

    @classdef.method('initialize')
    def method_initialize(self, space, w_arg1, w_arg2=None, block=None):
        try:
            typesym = Coerce.str(space, w_arg1)
            length = Coerce.int(space, w_arg2)
            self.init_str_int(space, typesym, length, block)
        except RubyError:
            length = Coerce.int(space, w_arg1)
            self.init_int(space, length, block)

    def init_str_int(self, space, typesym, length, block):
        size = rffi.sizeof(self.typesymbols[typesym])
        self.buffer = (length * size) * ['\x00']
        if block is not None:
            space.invoke_block(block, [space.newint(length)])

    def init_int(self, space, length, block):
        self.buffer = length * ['\x00']
        if block is not None:
            space.invoke_block(block, [space.newint(length)])

    @classdef.method('total')
    def method_total(self, space):
        return space.newint(len(self.buffer))

    # TODO: Once method_alias works in topaz, try the code in setup_class
    #       instead of this.
    @classdef.singleton_method('new_in')
    @classdef.singleton_method('new_out')
    @classdef.singleton_method('new_inout')
    @classdef.singleton_method('alloc_in')
    @classdef.singleton_method('alloc_out')
    @classdef.singleton_method('alloc_inout')
    def singleton_method_alloc_inout(self, space, args_w):
        return self.method_new(space, args_w, None)

    @classdef.method('put_char', offset='int', val='int')
    def method_put_char(self, space, offset, val):
        as_uchar = val + 127
        return self.method_put_uchar(space, offset, as_uchar)

    @classdef.method('get_char', offset='int')
    def method_get_char(self, space, offset):
        uchar = space.int_w(self.method_get_uchar(space, offset))
        val = uchar - 127
        return space.newint(val)

    @classdef.method('put_uchar', offset='int', val='int')
    def method_put_uchar(self, space, offset, val):
        self.buffer[offset] = chr(val)
        return self

    @classdef.method('get_uchar', offset='int')
    def method_get_uchar(self, space, offset):
        return space.newint(ord(self.buffer[offset]))

    @classdef.method('put_short', offset='int', val='int')
    def method_put_short(self, space, offset, val):
        as_ushort = val + 2**15 - 1
        return self.method_put_ushort(space, offset, as_ushort)

    @classdef.method('get_short', offset='int')
    def method_get_short(self, space, offset):
        ushort = space.int_w(self.method_get_ushort(space, offset))
        val = ushort - (2**15 - 1)
        return space.newint(val)

    @classdef.method('put_ushort', offset='int', val='int')
    def method_put_ushort(self, space, offset, val):
        byte0 = val % 256
        byte1 = val / 256
        self.buffer[offset+0] = chr(byte0)
        self.buffer[offset+1] = chr(byte1)
        return self

    @classdef.method('get_ushort', offset='int')
    def method_get_ushort(self, space, offset):
        byte0 = ord(self.buffer[offset+0])
        byte1 = ord(self.buffer[offset+1])
        return space.newint(  byte0 * 256**0
                            + byte1 * 256**1)

    @classdef.method('put_int', offset='int', val='int')
    def method_put_int(self, space, offset, val):
        as_uint = 2**31 - 1
        return self.method_put_uint(space, offset, val + as_uint)

    @classdef.method('get_int', offset='int')
    def method_get_int(self, space, offset):
        uint = space.int_w(self.method_get_uint(space, offset))
        val = uint - (2**31 - 1)
        return space.newint(val)

    @classdef.method('put_uint', offset='int', val='int')
    def method_put_uint(self, space, offset, val):
        byte = [val / 256**i % 256 for i in range(4)]
        for i in range(4):
            self.buffer[offset+i] = chr(byte[i])
        return self

    @classdef.method('get_uint', offset='int')
    def method_get_uint(self, space, offset):
        byte = [ord(x) for x in self.buffer[offset:offset+4]]
        return space.newint( sum([byte[i] * 256**i for i in range(4)]) )

    @classdef.method('put_long_long', offset='int', val='bigint')
    def method_put_long_long(self, space, offset, val):
        as_ulong_long = val.add(rbigint.fromlong(2**63))
        return self.method_put_ulong_long(space, offset, as_ulong_long)

    @classdef.method('get_long_long', offset='int')
    def method_get_long_long(self, space, offset):
        ulong_long = space.bigint_w(self.method_get_ulong_long(space, offset))
        long_long = ulong_long.sub(rbigint.fromlong(2**63))
        return space.newbigint_fromrbigint(long_long)

    @classdef.method('put_ulong_long', offset='int', val='bigint')
    def method_put_ulong_long(self, space, offset, val):
        rbi_256 = rbigint.fromint(256)
        rbi_range8 = [rbigint.fromint(i) for i in range(8)]
        byte = [val.div(rbi_256.pow(rbi)).mod(rbi_256)
                for rbi in rbi_range8]
        for i in range(8):
            self.buffer[offset+i] = chr(byte[i].toint())
        return self

    @classdef.method('get_ulong_long', offset='int')
    def method_get_ulong_long(self, space, offset):
        byte = [ord(x) for x in self.buffer[offset:offset+8]]
        val = sum([byte[i] * 256**i for i in range(8)])
        return space.newbigint_fromrbigint(rbigint.fromlong(val))

    @classdef.method('put_bytes', offset='int', val='str',
                                  index='int', length='int')
    def method_put_bytes(self, space, offset, val, index=0, length=-1):
        if index < 0 or len(val) <= index:
            raise space.error(space.w_IndexError,
                              "Tried to start at index %s of str %s" %
                              (index, val))
        if len(val) < index + length:
            raise space.error(space.w_IndexError,
                              "Tried to end at index %s of str %s" %
                              (index + length, val))
        val = val[index:] if length == -1 else val[index : index + length]
        for i, c in enumerate(val):
            self.buffer[offset+i] = val[i]
        return self

    @classdef.method('write_bytes', val='str', index='int', length='int')
    def method_write_bytes(self, space, val, index=0, length=-1):
        return self.method_put_bytes(space, 0, val, index, length)

    @classdef.method('get_bytes', offset='int', length='int')
    def method_get_bytes(self, space, offset, length):
        val = [self.buffer[offset+i] for i in range(length)]
        return space.newstr_fromchars(val)
