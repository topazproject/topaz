from topaz.objects.objectobject import W_Object
from topaz.coerce import Coerce
from topaz.error import RubyError
from topaz.module import ClassDef, check_frozen
from rpython.rlib.rbigint import rbigint
from rpython.rtyper.lltypesystem import rffi

def pow(x, y):
    e = 1
    for _ in range(y):
        e *= x
    return e

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
                   'double': rffi.DOUBLE,
                   'pointer': rffi.VOIDP}

    def __init__(self, space, klass=None):
        W_Object.__init__(self, space, klass)
        self.buffer = []

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        w_method_new = w_cls.getclass(space).find_method(space, 'new')
        w_cls.attach_method(space, 'alloc_inout', w_method_new)
        w_cls.attach_method(space, 'alloc_in', w_method_new)
        w_cls.attach_method(space, 'alloc_out', w_method_new)
        w_cls.attach_method(space, 'new_inout', w_method_new)
        w_cls.attach_method(space, 'new_in', w_method_new)
        w_cls.attach_method(space, 'new_out', w_method_new)
        space.send(w_cls, 'alias_method', [space.newsymbol('size'),
                                           space.newsymbol('total')])

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_BufferObject(space)

    @classdef.method('initialize', length='int')
    def method_initialize(self, space, w_str_or_int, length=1, block=None):
        try:
            typesym = Coerce.str(space, w_str_or_int)
            self.init_str_int(space, typesym, length, block)
        except RubyError, rubyerr:
            if rubyerr.w_value.is_kind_of(space, space.w_TypeError):
                length = Coerce.int(space, w_str_or_int)
                self.init_int(space, length, block)
            else:
                raise

    def init_str_int(self, space, typesym, length, block):
        if typesym not in self.typesymbols:
            raise space.error(space.w_ArgumentError,
                              "I don't know the %s type." % typesym)
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

    @classdef.method('put_char', offset='int', val='int')
    def method_put_char(self, space, offset, val):
        if val <= -128 or 128 <= val:
            raise space.error(space.w_TypeError,
                              "can't convert %s into a char" % val)
        as_uchar = val + 127
        return self.method_put_uchar(space, offset, as_uchar)

    @classdef.method('get_char', offset='int')
    def method_get_char(self, space, offset):
        uchar = space.int_w(self.method_get_uchar(space, offset))
        val = uchar - 127
        return space.newint(val)

    @classdef.method('put_uchar', offset='int', val='int')
    def method_put_uchar(self, space, offset, val):
        if val < 0 or 256 <= val:
            raise space.error(space.w_TypeError,
                              "can't convert %s into a uchar" % val)
        self.buffer[offset] = chr(val)
        return self

    @classdef.method('get_uchar', offset='int')
    def method_get_uchar(self, space, offset):
        if offset < 0:
            raise space.error(space.w_IndexError,
                              "Expected positive index")
        return space.newint(ord(self.buffer[offset]))

    @classdef.method('put_short', offset='int', val='int')
    def method_put_short(self, space, offset, val):
        if val <= -pow(2, 15) or pow(2, 15) <= val:
            raise space.error(space.w_TypeError,
                              "can't convert %s into a short" % val)
        as_ushort = val + pow(2, 15) - 1
        return self.method_put_ushort(space, offset, as_ushort)

    @classdef.method('get_short', offset='int')
    def method_get_short(self, space, offset):
        ushort = space.int_w(self.method_get_ushort(space, offset))
        val = ushort - (pow(2, 15) - 1)
        return space.newint(val)

    @classdef.method('put_ushort', offset='int', val='int')
    def method_put_ushort(self, space, offset, val):
        if val < 0 or pow(2, 16) <= val:
            raise space.error(space.w_TypeError,
                              "can't convert %s into a ushort" % val)
        byte0 = val % 256
        byte1 = val / 256
        self.buffer[offset+0] = chr(byte0)
        self.buffer[offset+1] = chr(byte1)
        return self

    @classdef.method('get_ushort', offset='int')
    def method_get_ushort(self, space, offset):
        if offset < 0:
            raise space.error(space.w_IndexError,
                              "Expected positive index")
        byte0 = ord(self.buffer[offset+0])
        byte1 = ord(self.buffer[offset+1])
        return space.newint(  byte0 * pow(256, 0)
                            + byte1 * pow(256, 1))

    @classdef.method('put_int', offset='int', val='int')
    def method_put_int(self, space, offset, val):
        if val <= -pow(2, 31) or pow(2, 31) <= val:
            raise space.error(space.w_TypeError,
                              "can't convert %s into an int" % val)
        as_uint = pow(2, 31) - 1
        return self.method_put_uint(space, offset, val + as_uint)

    @classdef.method('get_int', offset='int')
    def method_get_int(self, space, offset):
        uint = space.int_w(self.method_get_uint(space, offset))
        val = uint - (pow(2, 31) - 1)
        return space.newint(val)

    @classdef.method('put_uint', offset='int', val='int')
    def method_put_uint(self, space, offset, val):
        if val < 0 or pow(2, 32) <= val:
            raise space.error(space.w_TypeError,
                              "can't convert %s into a uint" % val)
        byte = [val / pow(256, i) % 256 for i in range(4)]
        for i in range(4):
            self.buffer[offset+i] = chr(byte[i])
        return self

    @classdef.method('get_uint', offset='int')
    def method_get_uint(self, space, offset):
        if offset < 0:
            raise space.error(space.w_IndexError,
                              "Expected positive index")
        byte = [ord(x) for x in self.buffer[offset:offset+4]]
        res = 0
        for i in range(4):
            res += byte[i] * pow(256, i)
        return space.newint(res)

    @classdef.method('put_long_long', offset='int', val='bigint')
    def method_put_long_long(self, space, offset, val):
        r_pow_2_63 = rbigint(digits=[0, 1], sign=1)
        if val.le(r_pow_2_63.neg()) or r_pow_2_63.le(val):
            raise space.error(space.w_TypeError,
                              "can't convert %s into a long long"
                              % val.repr()[:-1])
        as_ulong_long = val.add(r_pow_2_63)
        return self.method_put_ulong_long(space, offset, as_ulong_long)

    @classdef.method('get_long_long', offset='int')
    def method_get_long_long(self, space, offset):
        r_pow_2_63 = rbigint(digits=[0, 1], sign=1)
        ulong_long = space.bigint_w(self.method_get_ulong_long(space, offset))
        long_long = ulong_long.sub(r_pow_2_63)
        return space.newbigint_fromrbigint(long_long)

    @classdef.method('put_ulong_long', offset='int', val='bigint')
    def method_put_ulong_long(self, space, offset, val):
        r_0 = rbigint.fromint(0)
        r_pow_2_64 = rbigint(digits=[0, 2], sign=1)
        if val.lt(r_0) or r_pow_2_64.le(val):
            raise space.error(space.w_TypeError,
                              "can't convert %s into a ulong_long" %
                                  val.repr()[:-1])
        rbi_256 = rbigint.fromint(256)
        rbi_range8 = [rbigint.fromint(i) for i in range(8)]
        byte = [val.div(rbi_256.pow(rbi)).mod(rbi_256)
                for rbi in rbi_range8]
        for i in range(8):
            self.buffer[offset+i] = chr(byte[i].toint())
        return self

    @classdef.method('get_ulong_long', offset='int')
    def method_get_ulong_long(self, space, offset):
        if offset < 0:
            raise space.error(space.w_IndexError,
                              "Expected positive index")
        rbyte = [rbigint.fromint(ord(x)) for x in self.buffer[offset:offset+8]]
        val = rbigint.fromint(0)
        for i, rb in enumerate(rbyte):
            r_pow_256_i = rbigint.fromint(pow(256, i))
            val = val.add(rb.mul(r_pow_256_i))
        return space.newbigint_fromrbigint(val)

    @classdef.method('put_bytes', offset='int', val='str',
                                  index='int', length='int')
    @classdef.method('put_string', offset='int', val='str',
                                  index='int', length='int')
    def method_put_bytes(self, space, offset, val, index=0, length=-1):
        if length < -1:
            raise space.error(space.w_RangeError,
                              'Expected length to be -1 or positive')
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

    @classdef.method('get_string', offset='int', length='int')
    def method_get_string(self, space, offset, length):
        if offset < 0:
            raise space.error(space.w_IndexError, 'Expected positive offset')
        if length <= 0:
            raise space.error(space.w_RangeError,
                              'Expected positive and nonzero length')
        byte = self.buffer[offset:offset+length]
        str_end = byte.index('\x00') if '\x00' in byte else len(byte)-1
        val = byte[:str_end]
        return space.newstr_fromchars(val)
