from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object


class W_RegexpObject(W_Object):
    classdef = ClassDef("Regexp", W_Object.classdef)

    def __init__(self, space, regexp):
        W_Object.__init__(self, space)
        self.regexp = regexp

    @classdef.method("source")
    def method_source(self, space):
        return space.newstr_fromstr(self.regexp)
