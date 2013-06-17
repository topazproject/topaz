from topaz.objects.objectobject import W_Object
from topaz.module import ClassDef
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

    @classdef.method('initialize', typesym='symbol', length='int')
    def method_initialize(self, space, typesym, length):
        size = rffi.sizeof(self.typesymbols[typesym])
        self.buffer = (length * size) * ['\x00']

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
    @classdef.method('put_uchar', offset='int', val='int')
    def method_put_uchar(self, space, offset, val):
        self.buffer[offset] = chr(val)
        return self

    @classdef.method('get_char', offset='int')
    @classdef.method('get_uchar', offset='int')
    def method_get_uchar(self, space, offset):
        return space.newint(ord(self.buffer[offset]))

    @classdef.method('put_ushort', offset='int', val='int')
    def method_put_ushort(self, space, offset, val):
        most_significant = val / 256
        least_significant = val % 256
        self.buffer[offset] = chr(most_significant)
        self.buffer[offset+1] = chr(least_significant)
        return self

    @classdef.method('get_ushort', offset='int')
    def method_get_ushort(self, space, offset):
        most_significant = ord(self.buffer[offset])
        least_significant = ord(self.buffer[offset+1])
        return space.newint(  least_significant
                            + most_significant * 256)

    @classdef.method('put_uint', offset='int', val='int')
    def method_put_uint(self, space, offset, val):
        most_significant = val / 256 / 256
        middle_significant = val / 256 % 256
        least_significant = val % 256
        self.buffer[offset] = chr(most_significant)
        self.buffer[offset+1] = chr(middle_significant)
        self.buffer[offset+2] = chr(least_significant)

    @classdef.method('get_uint', offset='int')
    def method_get_uint(self, space, offset):
        most_significant = ord(self.buffer[offset])
        middle_significant = ord(self.buffer[offset+1])
        least_significant = ord(self.buffer[offset+2])
        return space.newint(  least_significant
                            + middle_significant * 256
                            + most_significant   * 256 * 256)

    @classdef.method('put_ulong_long', offset='int', val='int')
    def method_put_ulong_long(self, space, offset, val):
        most_significant = val / 256 / 256 / 256
        nearly_most_significant = val / 256 / 256 % 256
        nearly_least_significant = val / 256 % 256
        least_significant = val % 256
        self.buffer[offset] = chr(most_significant)
        self.buffer[offset+1] = chr(nearly_most_significant)
        self.buffer[offset+2] = chr(nearly_least_significant)
        self.buffer[offset+3] = chr(least_significant)

    @classdef.method('get_ulong_long', offset='int')
    def method_get_ulong_long(self, space, offset):
        most_significant = ord(self.buffer[offset])
        nearly_most_significant = ord(self.buffer[offset+1])
        nearly_least_significant = ord(self.buffer[offset+2])
        least_significant = ord(self.buffer[offset+3])
        return space.newint(  least_significant
                            + nearly_least_significant * 256
                            + nearly_most_significant  * 256 * 256
                            + most_significant         * 256 * 256 * 256)
