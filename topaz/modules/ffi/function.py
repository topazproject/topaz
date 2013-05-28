from topaz.objects.objectobject import W_Object
from topaz.module import ClassDef
from topaz.modules.ffi.type import W_TypeObject

class W_FunctionObject(W_Object):
    classdef = ClassDef('Function', W_Object.classdef)

    @classdef.singleton_method('allocate')
    def singleton_method_allocate(self, space, args_w):
        return W_FunctionObject(space)

    @classdef.method('initialize')
    def method_initialize(self, space, w_ret_type, w_arg_types, w_options):
        if not space.is_kind_of(w_ret_type, space.getclassfor(W_TypeObject)):
            if space.is_kind_of(w_ret_type, space.w_symbol):
                sym = space.symbol_w(w_ret_type)
                if sym.upper() in W_TypeObject.basics:
                    pass
                else:
                    raise space.error(space.w_TypeError,
                                      "can't convert Symbol into Type")
            else:
                tp = w_ret_type.getclass(space).name
                raise space.error(space.w_TypeError,
                                  "can't convert %s into Type" % tp)
