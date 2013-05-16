from topaz.objects.objectobject import W_Object
from topaz.module import ClassDef

class W_PointerObject(W_Object):
    classdef = ClassDef('Pointer', W_Object.classdef, filepath=__file__)

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_PointerObject(space)

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        space.set_const(w_cls, 'NULL', W_PointerObject(space))
