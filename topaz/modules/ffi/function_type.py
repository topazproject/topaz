from topaz.modules.ffi.type import W_TypeObject
from topaz.modules.ffi import type as ffitype
from topaz.modules.ffi._ruby_wrap_llval import (_ruby_wrap_number,
                                                _ruby_wrap_POINTER,
                                                _ruby_wrap_STRING,
                                                _ruby_wrap_llpointer_content,
                                                _ruby_unwrap_llpointer_content)
from topaz.module import ClassDef

def raise_TypeError_if_not_TypeObject(space, w_candidate):
    if not space.is_kind_of(w_candidate, space.getclassfor(W_TypeObject)):
        raise space.error(space.w_TypeError,
                          "Invalid parameter type (%s)" %
                          space.str_w(space.send(w_candidate, 'inspect')))

class W_FunctionTypeObject(W_TypeObject):
    classdef = ClassDef('FunctionType', W_TypeObject.classdef)

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_FunctionTypeObject(space)

    @classdef.method('initialize', arg_types_w='array')
    def method_initialize(self, space, w_ret_type, arg_types_w, w_options=None):
        if w_options is None:
            w_options = space.newhash()
        self.w_options = w_options

        raise_TypeError_if_not_TypeObject(space, w_ret_type)
        for w_arg_type in arg_types_w:
            raise_TypeError_if_not_TypeObject(space, w_arg_type)

        self.w_ret_type = w_ret_type
        self.arg_types_w = arg_types_w

    def invoke(self, space, w_proc, args_llp, llp_res):
        args_w = []
        for i in range(len(self.arg_types_w)):
            w_arg_type = self.arg_types_w[i]
            llp_arg = args_llp[i]
            t = w_arg_type.typeindex
            w_arg = _ruby_wrap_llpointer_content(space, llp_arg, t)
            args_w.append(w_arg)
        w_res = space.send(w_proc, 'call', args_w)
        t = self.w_ret_type.typeindex
        _ruby_unwrap_llpointer_content(space, w_res, llp_res, t)
