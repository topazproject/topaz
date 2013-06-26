from topaz.objects.objectobject import W_Object
from topaz.module import ClassDef
from topaz.modules.ffi.type import W_TypeObject
from topaz.modules.ffi.dynamic_library import W_DL_SymbolObject
from topaz.error import RubyError
from topaz.coerce import Coerce
from topaz.objects.functionobject import W_BuiltinFunction

from rpython.rtyper.lltypesystem import rffi
from rpython.rlib import clibffi

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
            return w_type
        try:
            sym = Coerce.symbol(space, w_type)
        except RubyError:
            tp = w_type.getclass(space).name
            raise space.error(space.w_TypeError,
                              "can't convert %s into Type" % tp)
        try:
            w_type_cls = space.getclassfor(W_TypeObject)
            return space.find_const(w_type_cls, sym.upper())
        except RubyError:
            raise space.error(space.w_TypeError,
                              "can't convert Symbol into Type")

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
            ffi_arg_types = [t.ffi_type for t in self.arg_types]
            ffi_ret_type = self.ret_type.ffi_type
            native_arg_types = [t.native_type for t in self.arg_types]
            native_ret_type = self.ret_type.native_type
            try:
                func_ptr = w_dl.cdll.getpointer(self.name,
                                                ffi_arg_types,
                                                ffi_ret_type)
                def attachment(lib, space, args_w, block):
                    args = [space.float_w(w_x) for w_x in args_w]
                    for argval, argtype in zip(args, native_arg_types):
                        casted_val = rffi.cast(argtype, argval)
                        func_ptr.push_arg(casted_val)
                    return space.newfloat(func_ptr.call(native_ret_type))
                method = W_BuiltinFunction(name, w_lib.getclass(space),
                                           attachment)
                w_lib.getclass(space).define_method(space, name, method)
            except KeyError: pass
