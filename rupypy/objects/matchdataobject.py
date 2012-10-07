from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object

class W_MatchDataObject(W_Object):
    classdef = ClassDef("MatchData", W_Object.classdef)

    def __init__(self, space, match):
        W_Object.__init__(self, space)
        self.match = match
