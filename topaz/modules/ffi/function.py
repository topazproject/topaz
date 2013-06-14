from topaz.objects.objectobject import W_Object
from topaz.module import ClassDef
from topaz.modules.ffi.type import W_TypeObject
from topaz.modules.ffi.dynamic_library import W_DL_SymbolObject
from topaz.error import RubyError
from topaz.coerce import Coerce
from topaz.objects.functionobject import W_BuiltinFunction

class W_FunctionObject(W_Object):
    classdef = ClassDef('Function', W_Object.classdef)

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_FunctionObject(space)

    @classdef.method('initialize')
    def method_initialize(self, space, w_ret_type, w_arg_types, w_name, w_options):
        self.ret_type = self.type_unwrap(space, w_ret_type)
        self.arg_types = [self.type_unwrap(space, w_type)
                          for w_type in space.listview(w_arg_types)]
        self.name = self.dlsym_unwrap(space, w_name)

    @staticmethod
    def type_unwrap(space, w_type):
        if space.is_kind_of(w_type, space.getclassfor(W_TypeObject)):
            return w_type.ffi_type
        try:
            sym = Coerce.symbol(space, w_type)
            key = sym.upper()
            if key in W_TypeObject.basics:
                return W_TypeObject.basics[key]
            else:
                raise space.error(space.w_TypeError,
                                  "can't convert Symbol into Type")
        except RubyError:
            tp = w_type.getclass(space).name
            raise space.error(space.w_TypeError,
                              "can't convert %s into Type" % tp)

    @staticmethod
    def dlsym_unwrap(space, w_name):
        if space.is_kind_of(w_name, space.getclassfor(W_DL_SymbolObject)):
            return w_name.symbol
        else:
            raise space.error(space.w_TypeError,
                              "can't convert %s into Symbol"
                              % w_name.getclass(space).name)

    @classdef.method('attach', name='str')
    def method_attach(self, space, w_lib, name):
        w_ffi_libs = space.find_instance_var(w_lib, '@ffi_libs')
        for w_dl in w_ffi_libs.listview(space):
            try:
                func_ptr = w_dl.cdll.getpointer(self.name,
                                                self.arg_types,
                                                self.ret_type)
                def attachment(self, space, args_w, block):
                    a, b = [space.int_w(w_x) for w_x in args_w]
                    return space.newint(a ** b)
                method = W_BuiltinFunction(name, w_lib.getclass(space),
                                           attachment)
                w_lib.getclass(space).define_method(space, name, method)
            except KeyError: pass
