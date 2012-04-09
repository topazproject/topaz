from rupypy.objects.base import W_Object


class W_IntObject(W_Object):
    def __init__(self, intvalue):
        self.intvalue = intvalue