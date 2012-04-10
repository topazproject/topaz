from rupypy.objects.objectobject import W_Object


class W_NilObject(W_Object):
    def is_true(self, space):
        return False
