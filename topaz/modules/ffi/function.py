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

    types = {'int8': rffi.CHAR,
             'uint8': rffi.UCHAR,
             'int16': rffi.SHORT,
             'uint16': rffi.USHORT,
             'int32': rffi.INT,
             'uint32': rffi.UINT,
             'long': rffi.LONG,
             'ulong': rffi.ULONG,
             'int64': rffi.LONGLONG,
             'uint64': rffi.ULONGLONG,
             'float32': rffi.FLOAT,
             'float64': rffi.DOUBLE,
             'void': rffi.VOIDP}

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
            return W_FunctionObject.types[w_type.native_type.lower()]
        try:
            sym = Coerce.symbol(space, w_type)
        except RubyError:
            tp = w_type.getclass(space).name
            raise space.error(space.w_TypeError,
                              "can't convert %s into Type" % tp)
        if sym in W_FunctionObject.types:
            return W_FunctionObject.types[sym]
        else:
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
            ffi_arg_types = [clibffi.cast_type_to_ffitype(t)
                             for t in self.arg_types]
            ffi_ret_type = clibffi.cast_type_to_ffitype(self.ret_type)
            try:
                func_ptr = w_dl.cdll.getpointer(self.name,
                                                ffi_arg_types,
                                                ffi_ret_type)
                def attachment(lib, space, args_w, block):
                    args = [space.float_w(w_x) for w_x in args_w]
                    for argval, argtype in zip(args, self.arg_types):
                        casted_val = rffi.cast(argtype, argval)
                        func_ptr.push_arg(casted_val)
                    return space.newfloat(func_ptr.call(self.ret_type))
                method = W_BuiltinFunction(name, w_lib.getclass(space),
                                           attachment)
                w_lib.getclass(space).define_method(space, name, method)
            except KeyError: pass
