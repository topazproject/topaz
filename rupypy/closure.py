from rupypy.objects.objectobject import W_Root


class BaseCell(W_Root):
    pass


class LocalCell(BaseCell):
    def get(self, frame, pos):
        return frame.localsstack_w[pos]

    def set(self, frame, pos, w_value):
        frame.localsstack_w[pos] = w_value

    def upgrade_to_closure(self, frame, pos):
        frame.cells[pos] = result = ClosureCell(self.get(frame, pos))
        return result


class ClosureCell(BaseCell):
    def __init__(self, w_value):
        self.w_value = w_value

    def get(self, frame, pos):
        return self.w_value

    def set(self, frame, pos, w_value):
        self.w_value = w_value

    def upgrade_to_closure(self, frame, pos):
        return self
