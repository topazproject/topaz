from topaz.objects.objectobject import W_Object
from topaz.module import ClassDef
from topaz.modules.ffi.type import W_TypeObject
from topaz.error import RubyError
from topaz.coerce import Coerce

class W_FunctionObject(W_Object):
    classdef = ClassDef('Function', W_Object.classdef)

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_FunctionObject(space)

    @classdef.method('initialize')
    def method_initialize(self, space, w_ret_type, w_arg_types, w_function, w_options):
        ret_type = self.type_unwrap(space, w_ret_type)
        arg_types = [self.type_unwrap(space, w_type)
                     for w_type in space.listview(w_arg_types)]
        # code for type object

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
