from topaz.objects.objectobject import W_Object
from topaz.module import ClassDef

class W_BufferObject(W_Object):
    classdef = ClassDef('Buffer', W_Object.classdef)

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        w_cls.method_attr_reader(space, [space.newsymbol('total')])

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_BufferObject(space)

    @classdef.method('initialize', typesym='symbol', length='int')
    def method_initialize(self, space, typesym, length):
        size = {'int': 4}[typesym]
        self.set_instance_var(space, '@total', space.newint(length * size))
