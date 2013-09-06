from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object
from topaz.modules.ffi.type import type_object

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
        self.w_name = self.dlsym_unwrap(space, w_name) if w_name else None
        space.send(self, 'init', [w_arg_types, space.newhash()])

    @staticmethod
    def dlsym_unwrap(space, w_name):
        try:
            return space.send(w_name, 'to_sym')
        except RubyError:
            raise space.error(space.w_TypeError,
                            "can't convert %s into FFI::DynamicLibrary::Symbol"
                              % w_name.getclass(space).name)

    @classdef.method('invoke')
    def method_invoke(self, space, args_w):
        return space.w_nil
