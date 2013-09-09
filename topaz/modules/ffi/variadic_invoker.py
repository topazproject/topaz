from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object
from topaz.modules.ffi.type import type_object, ffi_types
from topaz.modules.ffi.dynamic_library import coerce_dl_symbol
from topaz.modules.ffi.function import W_FunctionObject

from rpython.rlib import clibffi

class W_VariadicInvokerObject(W_Object):
    classdef = ClassDef('VariadicInvoker', W_Object.classdef)

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_VariadicInvokerObject(space)

    @classdef.method('initialize')
    def method_initialize(self, space, w_name, w_arg_types,
                          w_ret_type, w_options=None):
        if w_options is None: w_options = space.newhash()
        self.w_ret_type = type_object(space, w_ret_type)
        self.arg_types_w = [type_object(space, w_type)
                            for w_type in space.listview(w_arg_types)]
        self.funcsym = coerce_dl_symbol(space, w_name) if w_name else None
        space.send(self, 'init', [w_arg_types, space.newhash()])

    @classdef.method('invoke', arg_types_w='array', arg_values_w='array')
    def method_invoke(self, space, arg_types_w, arg_values_w):
        w_function = W_FunctionObject(space)
        w_function.arg_types_w = arg_types_w
        w_function.w_ret_type = self.w_ret_type
        ffi_arg_types = [ffi_types[t.name] for t in w_function.arg_types_w]
        ffi_ret_type = ffi_types[w_function.w_ret_type.name]
        w_function.ptr = self.funcsym
        w_function.funcptr = clibffi.FuncPtr('variadic',
                                             ffi_arg_types, ffi_ret_type,
                                             w_function.ptr)
        return space.send(w_function, 'call', arg_values_w)
