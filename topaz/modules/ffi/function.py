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
        self.w_ret_type = self.ensure_w_type(space, w_ret_type)
        self.arg_types_w = [self.ensure_w_type(space, w_type)
                          for w_type in space.listview(w_arg_types)]
        self.name = self.dlsym_unwrap(space, w_name)

    @staticmethod
    def ensure_w_type(space, w_type_or_sym):
        if space.is_kind_of(w_type_or_sym, space.getclassfor(W_TypeObject)):
            return w_type_or_sym
        try:
            sym = Coerce.symbol(space, w_type_or_sym)
        except RubyError:
            tp = w_type_or_sym.getclass(space).name
            raise space.error(space.w_TypeError,
                              "can't convert %s into Type" % tp)
        try:
            w_type_or_sym_cls = space.getclassfor(W_TypeObject)
            return space.find_const(w_type_or_sym_cls, sym.upper())
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
        # NOT RPYTHON
        # It defines a function: attachment (closures are not rpython)
        w_ffi_libs = space.find_instance_var(w_lib, '@ffi_libs')
        for w_dl in w_ffi_libs.listview(space):
            ffi_arg_types = [t.ffi_type for t in self.arg_types_w]
            ffi_ret_type = self.w_ret_type.ffi_type
            native_arg_types = [t.native_type for t in self.arg_types_w]
            native_ret_type = self.w_ret_type.native_type
            try:
                func_ptr = w_dl.cdll.getpointer(self.name,
                                                ffi_arg_types,
                                                ffi_ret_type)
                def attachment(lib, space, args_w, block):
                    args = [space.float_w(w_x) for w_x in args_w]
                    for argval, argtype in zip(args, native_arg_types):
                        casted_val = rffi.cast(argtype, argval)
                        func_ptr.push_arg(casted_val)
                    result = func_ptr.call(native_ret_type)
                    if ffi_ret_type in [clibffi.ffi_type_sint8,
                                        clibffi.ffi_type_uint8,
                                        clibffi.ffi_type_sint16,
                                        clibffi.ffi_type_uint16,
                                        clibffi.ffi_type_sint32,
                                        clibffi.ffi_type_uint32,
                                        clibffi.ffi_type_sint64,
                                        clibffi.ffi_type_uint64]:
                        return space.newint_or_bigint(result)
                    elif ffi_ret_type in [clibffi.ffi_type_float,
                                          clibffi.ffi_type_double]:
                        return space.newfloat(result)
                method = W_BuiltinFunction(name, w_lib.getclass(space),
                                           attachment)
                w_lib.getclass(space).define_method(space, name, method)
            except KeyError: pass
