from rupypy.objects.objectobject import W_Object


class W_TrueObject(W_Object):
    pass

class W_FalseObject(W_Object):
    def is_true(self, space):
        return False
