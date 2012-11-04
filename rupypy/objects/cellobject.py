from rupypy.objects.objectobject import W_BaseObject


class W_CellObject(W_BaseObject):
    def __init__(self):
        self.w_value = None

    def get(self):
        return self.w_value

    def set(self, w_value):
        self.w_value = w_value
