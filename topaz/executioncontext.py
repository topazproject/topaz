from rpython.rlib import jit, rthread
from rpython.rlib.objectmodel import not_rpython, we_are_translated

from topaz.error import RubyError
from topaz.frame import Frame
from topaz.objects.fiberobject import W_FiberObject


class ThreadLocals(object):
    # Inspired by Pypy's OSThreadLocals (but without weaklist optimization)

    @not_rpython
    def __init__(self):
        self._valuedict = {}
        self._cleanup_()
        self.raw_thread_local = rthread.ThreadLocalReference(
            ExecutionContext, loop_invariant=True)

    def get_ec(self):
        ec = self.raw_thread_local.get()
        if not we_are_translated():
            assert ec is self._valuedict.get(rthread.get_ident(), None)
        return ec

    def _cleanup_(self):
        self._valuedict.clear()
        self._mainthreadident = 0

    def enter_thread(self):
        "Notification that the current thread is about to start running."
        self._set_ec(ExecutionContext())

    def try_enter_thread(self):
        # common case: the thread-local has already got a value
        if self.raw_thread_local.get() is not None:
            return False

        # Else, make and attach a new ExecutionContext
        ec = ExecutionContext()
        self._set_ec(ec)
        return True

    def _set_ec(self, ec, register_in_valuedict=True):
        ident = rthread.get_ident()
        if self._mainthreadident == 0 or self._mainthreadident == ident:
            ec._signals_enabled = 1    # the main thread is enabled
            self._mainthreadident = ident
        if register_in_valuedict:
            self._valuedict[ident] = ec
        self.raw_thread_local.set(ec)

    def leave_thread(self):
        "Notification that the current thread is about to stop."
        ec = self.get_ec()
        if ec is not None:
            try:
                self.thread_is_stopping(ec)
            finally:
                self.raw_thread_local.set(None)
                ident = rthread.get_ident()
                try:
                    del self._valuedict[ident]
                except KeyError:
                    pass

    @staticmethod
    def thread_is_stopping(ec):
        tlobjs = ec._thread_local_objs
        if tlobjs is None:
            return
        ec._thread_local_objs = None
        for wref in tlobjs.items():
            local = wref()
            if local is not None:
                del local.dicts[ec]
                local.last_dict = None
                local.last_ec = None


class ExecutionContext(object):
    _immutable_fields_ = ["w_trace_proc?"]
    _thread_local_objs = None

    def __init__(self):
        self.topframeref = jit.vref_None
        self.last_instr = -1
        self.w_trace_proc = None
        self.in_trace_proc = False
        self.recursive_calls = {}
        self.catch_names = {}

        self.fiber_thread = None
        self.w_main_fiber = None

    def getmainfiber(self, space):
        if self.w_main_fiber is None:
            self.w_main_fiber = W_FiberObject.build_main_fiber(space, self)
        return self.w_main_fiber

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
                space.send(self.w_trace_proc, "call", [
                    space.newstr_fromstr(event),
                    space.newstr_fromstr(frame.bytecode.filepath),
                    space.newint(
                        frame.bytecode.lineno_table[frame.last_instr]),
                    (space.newstr_fromstr(scope_id)
                        if scope_id is not None else space.w_nil),
                    space.newbinding_fromframe(frame),
                    (space.newstr_fromstr(classname)
                        if classname is not None else space.w_nil),
                ])
            finally:
                self.in_trace_proc = False

    def enter(self, frame):
        frame.backref = self.topframeref
        if self.last_instr != -1:
            frame.back_last_instr = self.last_instr
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

    def recursion_guard(self, func_id, w_obj):
        # We need independent recursion detection for different blocks of
        # potentially recursive code so that they don't interfere with each
        # other and cause false positives. This is only likely to be a problem
        # if one recursion-guarded function calls another, but we can't
        # guarantee that won't happen.
        return _RecursionGuardContextManager(self, func_id, w_obj)

    def catch_block(self, name):
        return _CatchContextManager(self, name)

    def is_in_catch_block_for_name(self, name):
        return name in self.catch_names


class _VisitFrameContextManager(object):
    def __init__(self, ec, frame):
        self.ec = ec
        self.frame = frame

    def __enter__(self):
        self.ec.enter(self.frame)

    def __exit__(self, exc_type, exc_value, tb):
        ruby_exception = False
        if exc_value is not None and isinstance(exc_value, RubyError):
            ruby_exception = True
            if exc_value.w_value.frame is None:
                exc_value.w_value.frame = self.frame

        self.ec.leave(self.frame, ruby_exception)


class _RecursionGuardContextManager(object):
    def __init__(self, ec, func_id, w_obj):
        self.ec = ec
        if func_id not in self.ec.recursive_calls:
            self.ec.recursive_calls[func_id] = {}
        self.recursive_objects = self.ec.recursive_calls[func_id]
        self.func_id = func_id
        self.w_obj = w_obj
        self.added = False

    def __enter__(self):
        if self.w_obj in self.recursive_objects:
            return True
        self.recursive_objects[self.w_obj] = None
        self.added = True
        return False

    def __exit__(self, exc_type, exc_value, tb):
        if self.added:
            del self.recursive_objects[self.w_obj]
            if not self.recursive_objects:
                del self.ec.recursive_calls[self.func_id]


class _CatchContextManager(object):
    """This context manager tracks which symbol names we're in catch blocks for
    so that we can raise an appropriate Ruby exception when app-level code
    tries to throw a symbol we're catching. When catch blocks for the same
    symbol are nested, we only care about the outermost one.
    """
    def __init__(self, ec, catch_name):
        self.ec = ec
        self.catch_name = catch_name
        self.added = False

    def __enter__(self):
        if self.catch_name in self.ec.catch_names:
            return
        self.ec.catch_names[self.catch_name] = None
        self.added = True

    def __exit__(self, exc_type, exc_value, tb):
        if self.added:
            del self.ec.catch_names[self.catch_name]
