from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object


class W_EncodingObject(W_Object):
    classdef = ClassDef("Encoding", W_Object.classdef)

    @classdef.singleton_method("default_external")
    def singleton_method_default_external(self, space):
        return W_EncodingObject(space)

    @classdef.singleton_method("default_internal")
    def singleton_method_default_internal(self, space):
        return W_EncodingObject(space)

    @classdef.singleton_method("default_internal=")
    def singleton_method_set_default_internal(self, space, w_enc):
        pass

    @classdef.singleton_method("default_external=")
    def singleton_method_set_default_external(self, space, w_enc):
        pass

    @classdef.singleton_method("aliases")
    def singleton_method_aliases(self, space):
        return space.newarray([])

    @classdef.singleton_method("name_list")
    def singleton_method_name_list(self, space):
        return space.newarray([])
