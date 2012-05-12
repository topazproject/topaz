class ExecutionContext(object):
    def __init__(self, space):
        self.space = space
        self.topframeref = None

    def enter(self, frame):
        frame.backref = self.topframeref
        self.topframeref = frame

    def leave(self, frame):
        self.topframeref = frame.backref
