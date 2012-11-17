from rupypy.objects.objectobject import W_Root


class BaseCell(W_Root):
    pass


class ClosureCell(BaseCell):
    def __init__(self, w_value):
        self.w_value = w_value

    def get(self, space, frame, pos):
        return self.w_value

    def set(self, space, frame, pos, w_value):
        self.w_value = w_value
