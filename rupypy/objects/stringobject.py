from rupypy.objects.objectobject import W_Object


class W_StringObject(W_Object):
    def __init__(self, chars):
        self.chars = chars

    def str_w(self, space):
        return "".join(self.chars)

    def liststr_w(self, space):
        return self.chars