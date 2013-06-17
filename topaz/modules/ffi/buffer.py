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
        self.buffer = (length * size) * [0]

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

    @classdef.method('put_char', offset='int', char='int')
    def method_put_char(self, space, offset, char):
        self.buffer[offset] = char

    @classdef.method('get_char', offset='int')
    def method_get_char(self, space, offset):
        return space.newint(self.buffer[offset])
