from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object
from topaz.coerce import Coerce

class W_DynamicLibraryObject(W_Object):
    classdef = ClassDef('DynamicLibrary', W_Object.classdef, filepath=__file__)

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        space.set_const(w_cls, "RTLD_LAZY", space.newint(1))
        space.set_const(w_cls, "RTLD_NOW", space.newint(2))
        space.set_const(w_cls, "RTLD_GLOBAL", space.newint(257))
        space.set_const(w_cls, "RTLD_LOCAL", space.newint(0))

    @classdef.singleton_method('open', flags='int')
    def method_open(self, space, w_name, flags):
        if w_name == space.w_nil:
            name = None
        else:
            name = Coerce.path(space, w_name)
        return W_DynamicLibraryObject(space)
