from topaz.module import ModuleDef

# A rather abstract base class
class DataConverter(object):
    moduledef = ModuleDef('DataConverter')

    # TODO: If no args given raise NotIMplemented error
    #       (see MRI ffi for error message)
    #       If one arg is given use find_type to figure out the type
    #       Then save the result as ruby attr (@native_type) and return it.
    #       If more arguments were given raise ArgumentError
    @moduledef.function('native_type')
    def native_type(self, space, args_w): pass

    @moduledef.function('to_native')
    def to_native(self, space, w_value, w_ctx):
        return w_value

    @moduledef.function('from_native')
    def from_native(self, space, w_value, w_ctx):
        return w_value
