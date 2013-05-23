from topaz.module import ModuleDef

class DataConverter(object):
    moduledef = ModuleDef('DataConverter')

    @moduledef.function('native_type')
    def native_type(self, space, args_w): pass

    @moduledef.function('to_native')
    def to_native(self, space): pass

    @moduledef.function('from_native')
    def from_native(self, space): pass
