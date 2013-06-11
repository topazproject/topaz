from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object
from topaz.coerce import Coerce

from rpython.rlib import clibffi

class W_DynamicLibraryObject(W_Object):
    classdef = ClassDef('DynamicLibrary', W_Object.classdef)

    def __deepcopy__(self, memo):
        obj = super(W_TypeObject, self).__deepcopy__(memo)
        obj.handle = self.handle
        return obj

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        space.set_const(w_cls, "RTLD_LAZY", space.newint(1))
        space.set_const(w_cls, "RTLD_NOW", space.newint(2))
        space.set_const(w_cls, "RTLD_GLOBAL", space.newint(257))
        space.set_const(w_cls, "RTLD_LOCAL", space.newint(0))
        space.set_const(w_cls, 'Symbol', space.getclassfor(W_DL_SymbolObject))

    def __init__(self, space, name, flags, klass=None):
        W_Object.__init__(self, space, klass)
        namestr = '[current process]' if name is None else name
        try:
            self.cdll = clibffi.CDLL(name, flags)
        except clibffi.DLOpenError:
            raise space.error(space.w_LoadError,
                              "Could not open library %s" % namestr)
        self.set_instance_var(space, '@name', space.newsymbol(namestr))

    @classdef.singleton_method('new', flags='int')
    @classdef.singleton_method('open', flags='int')
    def singleton_method_new(self, space, w_name, flags=0):
        name = (Coerce.path(space, w_name) if w_name is not space.w_nil
                else None)
        lib = W_DynamicLibraryObject(space, name, flags)
        return lib

    @classdef.method('find_variable', name='symbol')
    def method_find_variable(self, space, name):
        w_sym = space.find_const(self.getclass(space), 'Symbol')
        # TODO: return an instance of the class w_sym instead of just w_sym
        return w_sym.method_new(space, [], None)

    @classdef.method('find_function', name='symbol')
    def method_find_function(self, space, name):
        return self.method_find_variable(space, name)

class W_DL_SymbolObject(W_Object):
    classdef = ClassDef('Symbol', W_Object.classdef)

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_DL_SymbolObject(space)

    @classdef.method('null?')
    def method_null_p(self, space):
        return space.newbool(True)
