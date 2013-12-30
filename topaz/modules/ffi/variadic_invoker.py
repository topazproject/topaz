from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object
from topaz.modules.ffi.type import type_object, ffi_types, W_TypeObject, VOID
from topaz.modules.ffi.dynamic_library import coerce_dl_symbol
from topaz.modules.ffi.function_type import W_FunctionTypeObject
from topaz.modules.ffi.function import W_FFIFunctionObject

from rpython.rlib import clibffi
from rpython.rlib import jit
from rpython.rtyper.lltypesystem import lltype, rffi

class W_VariadicInvokerObject(W_Object):
    classdef = ClassDef('VariadicInvoker', W_Object.classdef)

    def __init__(self, space):
        W_Object.__init__(self, space)
        self.w_info = None
        self.w_handle = None

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_VariadicInvokerObject(space)

    @classdef.method('initialize')
    def method_initialize(self, space, w_handle, w_arg_types,
                          w_ret_type, w_options=None):
        self.w_ret_type = w_ret_type
        self.w_options = w_options
        self.w_handle = w_handle
        if w_options is None:
            w_type_map = space.newhash()
        else:
            w_key = space.newsymbol('type_map')
            w_type_map = space.send(w_options, '[]', [w_key])
        space.send(self, 'init', [w_arg_types, w_type_map])

    @classdef.method('invoke', arg_values_w='array')
    def method_invoke(self, space, w_arg_types, arg_values_w):
        w_func_cls = space.getclassfor(W_FFIFunctionObject)
        w_func = space.send(w_func_cls, 'new',
                            [self.w_ret_type, w_arg_types,
                            self.w_handle, self.w_options])
        return self._dli_call(space, w_func, arg_values_w)

    @jit.dont_look_inside
    def _dli_call(self, space, w_func, arg_values_w):
        # XXX we are missing argument promotion for the variadic arguments here
        # see
        # http://stackoverflow.com/questions/1255775/default-argument-promotions-in-c-function-calls
        return space.send(w_func, 'call', arg_values_w)
