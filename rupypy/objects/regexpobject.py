from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_BaseObject


class W_RegexpObject(W_BaseObject):
    classdef = ClassDef("Regexp", W_BaseObject.classdef)

    def __init__(self, regexp):
        self.regexp = regexp

    @classdef.method("source")
    def method_source(self, space):
        return space.newstr_fromstr(self.regexp)
