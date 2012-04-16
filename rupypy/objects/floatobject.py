from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_BaseObject


class W_FloatObject(W_BaseObject):
    def __init__(self, floatvalue):
        self.floatvalue = floatvalue

    def float_w(self, space):
        return self.floatvalue