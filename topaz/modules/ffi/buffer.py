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
        w_cls.method_attr_reader(space, [space.newsymbol('total')])

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_BufferObject(space)

    @classdef.method('initialize', typesym='symbol', length='int')
    def method_initialize(self, space, typesym, length):
        size = rffi.sizeof(self.typesymbols[typesym])
        self.set_instance_var(space, '@total', space.newint(length * size))
