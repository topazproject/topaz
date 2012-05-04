class RubyError(Exception):
    def __init__(self, w_value):
        self.w_value = w_value
