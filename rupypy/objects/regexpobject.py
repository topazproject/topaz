from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object, W_BuiltinObject


class W_RegexpObject(W_BuiltinObject):
    classdef = ClassDef("Regexp", W_Object.classdef)

    def __init__(self, space, regexp):
        W_BuiltinObject.__init__(self, space)
        self.regexp = regexp

    @classdef.method("source")
    def method_source(self, space):
        return space.newstr_fromstr(self.regexp)
