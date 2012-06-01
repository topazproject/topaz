from pypy.rlib import jit

from rupypy.error import RubyError


class ExecutionContext(object):
    def __init__(self, space):
        self.space = space
        self.topframeref = jit.vref_None

    def enter(self, frame):
        frame.backref = self.topframeref
        self.topframeref = jit.virtual_ref(frame)

    def leave(self, frame, got_exception):
        frame_vref = self.topframeref
        self.topframeref = frame.backref
        if frame.escaped or got_exception:
            back = frame.backref()
            if back is not None:
                back.escaped = True
            frame_vref()
        jit.virtual_ref_finish(frame_vref, frame)

    def visit_frame(self, frame, append_instr=False):
        return _VisitFrameContextManager(self, frame, append_instr)


class _VisitFrameContextManager(object):
    def __init__(self, ec, frame, append_instr):
        self.ec = ec
        self.frame = frame
        self.append_instr = append_instr

    def __enter__(self):
        self.ec.enter(self.frame)

    def __exit__(self, exc_type, exc_value, tb):
        if exc_value is not None and isinstance(exc_value, RubyError):
            if exc_value.w_value.frame is None:
                exc_value.w_value.frame = self.frame
            if self.append_instr:
                exc_value.w_value.last_instructions.append(-1)

        self.ec.leave(self.frame, exc_value is not None)
