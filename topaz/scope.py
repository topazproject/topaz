import copy


class StaticScope(object):
    _immutable_fields_ = ["w_mod", "backscope"]

    def __init__(self, w_mod, backscope):
        self.w_mod = w_mod
        self.backscope = backscope

    def __deepcopy__(self, memo):
        return StaticScope(
            copy.deepcopy(self.w_mod, memo),
            copy.deepcopy(self.backscope, memo))
