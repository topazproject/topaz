from pypy.rlib import jit

from topaz.error import RubyError
from topaz.frame import Frame


class IntegerWrapper(object):
    def __init__(self, value):
        self.value = value


class ExecutionContext(object):
    _immutable_fields_ = ["w_trace_proc?"]

    def __init__(self):
        self.topframeref = jit.vref_None
        self.last_instr_ref = None
        self.regexp_match_cell = None
        self.w_trace_proc = None
        self.in_trace_proc = False

    def settraceproc(self, w_proc):
        self.w_trace_proc = w_proc

    def gettraceproc(self):
        return self.w_trace_proc

    def hastraceproc(self):
        return self.w_trace_proc is not None and not self.in_trace_proc

    def invoke_trace_proc(self, space, event, scope_id, classname, frame=None):
        if self.hastraceproc():
            self.in_trace_proc = True
            try:
                if frame is None:
                    frame = self.gettoprubyframe()
                space.send(self.w_trace_proc, space.newsymbol("call"), [
                    space.newstr_fromstr(event),
                    space.newstr_fromstr(frame.bytecode.filepath),
                    space.newint(frame.bytecode.lineno_table[frame.last_instr]),
                    space.newstr_fromstr(scope_id) if scope_id is not None else space.w_nil,
                    space.newbinding_fromframe(frame),
                    space.newstr_fromstr(classname) if classname is not None else space.w_nil,
                ])
            finally:
                self.in_trace_proc = False

    def enter(self, frame):
        frame.backref = self.topframeref
        if self.last_instr_ref is not None:
            frame.back_last_instr = self.last_instr_ref.value
            self.last_instr_ref = None
        self.topframeref = jit.virtual_ref(frame)
        if isinstance(frame, Frame):
            self.regexp_match_cell = frame.regexp_match_cell

    def leave(self, frame, got_exception, original_regexp_match_cell):
        frame_vref = self.topframeref
        self.topframeref = frame.backref
        if frame.escaped or got_exception:
            back = frame.backref()
            if back is not None:
                back.escaped = True
            frame_vref()
        jit.virtual_ref_finish(frame_vref, frame)
        self.regexp_match_cell = original_regexp_match_cell

    def visit_frame(self, frame):
        return _VisitFrameContextManager(self, frame)

    def gettopframe(self):
        return self.topframeref()

    @jit.unroll_safe
    def gettoprubyframe(self):
        frame = self.gettopframe()
        while frame is not None and not isinstance(frame, Frame):
            frame = frame.backref()
        return frame


class _VisitFrameContextManager(object):
    def __init__(self, ec, frame):
        self.ec = ec
        self.frame = frame

    def __enter__(self):
        self.original_regexp_match_cell = self.ec.regexp_match_cell
        self.ec.enter(self.frame)

    def __exit__(self, exc_type, exc_value, tb):
        if exc_value is not None and isinstance(exc_value, RubyError):
            if exc_value.w_value.frame is None:
                exc_value.w_value.frame = self.frame

        self.ec.leave(self.frame, exc_value is not None, self.original_regexp_match_cell)
