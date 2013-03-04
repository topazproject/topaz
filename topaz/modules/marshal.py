from __future__ import absolute_import
from topaz.module import Module, ModuleDef
import marshal


class Marshal(Module):
    moduledef = ModuleDef("Marshal", filepath=__file__)

    @moduledef.setup_module
    def setup_module(space, w_mod):
        pass

    @moduledef.function("dump")
    def method_dump(self, space, w_obj):
        return space.newstr_fromstr(marshal.dumps(space.int_w(w_obj)))

    @moduledef.function("load")
    def method_load(self, space, w_obj):
        return space.newint(marshal.loads(space.str_w(w_obj)))
