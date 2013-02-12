from topaz.objects.objectobject import W_Root
from topaz.objects.intobject import W_FixnumObject


class BaseCell(W_Root):
    pass


class LocalCell(BaseCell):
    def get(self, space, frame, pos):
        return frame.localsstack_w[pos]

    def set(self, space, frame, pos, w_value):
        frame.localsstack_w[pos] = w_value

    def upgrade_to_closure(self, space, frame, pos):
        w_obj = self.get(space, frame, pos)
        if isinstance(w_obj, W_FixnumObject):
            frame.cells[pos] = result = IntCell(space.int_w(w_obj))
        else:
            frame.cells[pos] = result = ClosureCell(w_obj)
        return result


class ClosureCell(BaseCell):
    def __init__(self, w_value):
        self.w_value = w_value

    def get(self, space, frame, pos):
        return self.w_value

    def set(self, space, frame, pos, w_value):
        self.w_value = w_value

    def upgrade_to_closure(self, space, frame, pos):
        return self


class IntCell(ClosureCell):
    def __init__(self, intvalue):
        ClosureCell.__init__(self, None)
        self.intvalue = intvalue

    def get(self, space, frame, pos):
        if self.w_value is None:
            return space.newint(self.intvalue)
        else:
            return ClosureCell.get(self, space, frame, pos)

    def set(self, space, frame, pos, w_value):
        if isinstance(w_value, W_FixnumObject):
            self.intvalue = space.int_w(w_value)
            self.w_value = None
        else:
            ClosureCell.set(self, space, frame, pos, w_value)
