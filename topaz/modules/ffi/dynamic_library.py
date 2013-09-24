from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object
from topaz.modules.ffi.pointer import W_PointerObject
from topaz.coerce import Coerce

from rpython.rlib import clibffi
from rpython.rtyper.lltypesystem import rffi

class W_DynamicLibraryObject(W_Object):
    classdef = ClassDef('DynamicLibrary', W_Object.classdef)

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        space.set_const(w_cls, "RTLD_LAZY", space.newint(1))
        space.set_const(w_cls, "RTLD_NOW", space.newint(2))
        space.set_const(w_cls, "RTLD_GLOBAL", space.newint(257))
        space.set_const(w_cls, "RTLD_LOCAL", space.newint(0))
        space.set_const(w_cls, 'Symbol', space.getclassfor(W_DL_SymbolObject))

        w_method_new = w_cls.getclass(space).find_method(space, 'new')
        w_cls.attach_method(space, 'open', w_method_new)
        space.send(w_cls, 'alias_method', [space.newsymbol('find_function'),
                                           space.newsymbol('find_variable')])

    def __init__(self, space, name, flags, klass=None):
        W_Object.__init__(self, space, klass)
        namestr = '[current process]' if name is None else name
        # on my os it's libc.so.6, not just libc.so
        if name == 'libc.so': name = 'libc.so.6'
        try:
            self.cdll = clibffi.CDLL(name, flags)
        except clibffi.DLOpenError:
            raise space.error(space.w_LoadError,
                              "Could not open library %s" % namestr)
        self.set_instance_var(space, '@name', space.newsymbol(namestr))

    def getpointer(self, name, ffi_arg_types, ffi_ret_types):
        return self.cdll.getpointer(name,
                                    ffi_arg_types,
                                    ffi_ret_types)

    @classdef.singleton_method('new', flags='int')
    def singleton_method_new(self, space, w_name, flags=0):
        name = (Coerce.path(space, w_name)
                if w_name is not space.w_nil
                else None)
        lib = W_DynamicLibraryObject(space, name, flags)
        return lib

    @classdef.method('find_variable', name='symbol')
    def method_find_variable(self, space, name):
        funcsym = self.cdll.getaddressindll(name)
        w_sym = space.find_const(space.getclass(self), 'Symbol')
        return W_DL_SymbolObject(space, funcsym)

def coerce_dl_symbol(space, w_name):
    if isinstance(w_name, W_DL_SymbolObject):
        return w_name.ptr
    else:
        raise space.error(space.w_TypeError,
                        "can't convert %s into FFI::DynamicLibrary::Symbol"
                          % w_name.getclass(space).name)

class W_DL_SymbolObject(W_PointerObject):
    classdef = ClassDef('Symbol', W_PointerObject.classdef)

    def __init__(self, space, funcsym, klass=None):
        W_PointerObject.__init__(self, space, klass)
        self.ptr = funcsym

    # TODO: new method should be private!
    #       or: should take an int and try to make a voidptr out of it.

    #@classdef.singleton_method('allocate')
    #def singleton_method_allocate(self, space, args_w):
    #    return W_DL_SymbolObject(space)
