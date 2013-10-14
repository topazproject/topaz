from topaz.module import ModuleDef
from topaz.modules.ffi.type import type_object

# A rather abstract base class
class DataConverter(object):
    moduledef = ModuleDef('DataConverter')

    @moduledef.function('native_type')
    def native_type(self, space, args_w):
        if len(args_w) == 0:
            raise space.error(space.w_NotImplementedError,
                              "native_type method not overridden and no"
                              "native_type set")
        elif len(args_w) == 1:
            w_arg_as_type = type_object(space, args_w[0])
            space.set_instance_var(self, '@native_type', w_arg_as_type)
            return w_arg_as_type
        raise space.error(space.w_ArgumentError, "incorrect arguments")

    @moduledef.function('to_native')
    def to_native(self, space, w_value, w_ctx):
        return w_value

    @moduledef.function('from_native')
    def from_native(self, space, w_value, w_ctx):
        return w_value
