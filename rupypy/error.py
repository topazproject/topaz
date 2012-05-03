class RubyError(Exception):
    def __init__(self, w_type, msg):
        self.w_type = w_type
        self.msg = msg