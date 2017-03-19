import sys

from rpython.rlib import jit, objectmodel
from rpython.rlib.unroll import unrolling_iterable

from topaz.error import RubyError
from topaz.frame import Frame
from topaz.objects.fiberobject import W_FiberObject

TICK_COUNTER_STEP = 100


class ExecutionContext(object):
    _immutable_fields_ = ["w_trace_proc?"]

    def __init__(self):
        self.topframeref = jit.vref_None
        self.last_instr = -1
        self.w_trace_proc = None
        self.in_trace_proc = False
        self.recursive_calls = {}
        self.catch_names = {}

        self.fiber_thread = None
        self.w_main_fiber = None

    @staticmethod
    def _mark_thread_disappeared(space):
        # Called in the child process after os.fork() by interp_posix.py.
        # Marks all ExecutionContexts except the current one
        # with 'thread_disappeared = True'.
        me = space.getexecutioncontext()
        for ec in space.threadlocals.getallvalues().values():
            if ec is not me:
                ec.thread_disappeared = True

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

    def invoke_only_trace_proc(self, space, event, scope_id, classname,
                               frame=None):
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

    def invoke_trace_proc(self, space, event, scope_id, classname, frame=None,
                          decr_by=TICK_COUNTER_STEP):
        self.invoke_only_trace_proc(space, event, scope_id, classname, frame)
        actionflag = space.actionflag
        if actionflag.decrement_ticker(decr_by) < 0:
            actionflag.action_dispatcher(self, frame)

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


class AbstractActionFlag(object):
    """This holds in an integer the 'ticker'.  If threads are enabled,
    it is decremented at each bytecode; when it reaches zero, we release
    the GIL.  And whether we have threads or not, it is forced to zero
    whenever we fire any of the asynchronous actions.
    """

    _immutable_fields_ = ["checkinterval_scaled?"]

    def __init__(self):
        self._periodic_actions = []
        self._nonperiodic_actions = []
        self.has_bytecode_counter = False
        self.fired_actions = None
        # the default value is not 100, unlike CPython 2.7, but a much
        # larger value, because we use a technique that not only allows
        # but actually *forces* another thread to run whenever the counter
        # reaches zero.
        self.checkinterval_scaled = 10000 * TICK_COUNTER_STEP
        self._rebuild_action_dispatcher()

    def fire(self, action):
        """Request for the action to be run before the next opcode."""
        if not action._fired:
            action._fired = True
            if self.fired_actions is None:
                self.fired_actions = []
            self.fired_actions.append(action)
            # set the ticker to -1 in order to force action_dispatcher()
            # to run at the next possible bytecode
            self.reset_ticker(-1)

    def register_periodic_action(self, action, use_bytecode_counter):
        """NOT_RPYTHON:
        Register the PeriodicAsyncAction action to be called whenever the
        tick counter becomes smaller than 0.  If 'use_bytecode_counter' is
        True, make sure that we decrease the tick counter at every bytecode.
        This is needed for threads.  Note that 'use_bytecode_counter' can be
        False for signal handling, because whenever the process receives a
        signal, the tick counter is set to -1 by C code in signals.h.
        """
        assert isinstance(action, PeriodicAsyncAction)
        # hack to put the release-the-GIL one at the end of the list,
        # and the report-the-signals one at the start of the list.
        if use_bytecode_counter:
            self._periodic_actions.append(action)
            self.has_bytecode_counter = True
        else:
            self._periodic_actions.insert(0, action)
        self._rebuild_action_dispatcher()

    def getcheckinterval(self):
        return self.checkinterval_scaled // TICK_COUNTER_STEP

    def setcheckinterval(self, interval):
        MAX = sys.maxint // TICK_COUNTER_STEP
        if interval < 1:
            interval = 1
        elif interval > MAX:
            interval = MAX
        self.checkinterval_scaled = interval * TICK_COUNTER_STEP
        self.reset_ticker(-1)

    def _rebuild_action_dispatcher(self):
        periodic_actions = unrolling_iterable(self._periodic_actions)

        @jit.unroll_safe
        @objectmodel.dont_inline
        def action_dispatcher(ec, frame):
            # periodic actions (first reset the bytecode counter)
            self.reset_ticker(self.checkinterval_scaled)
            for action in periodic_actions:
                action.perform(ec, frame)

            # nonperiodic actions
            actions = self.fired_actions
            if actions is not None:
                self.fired_actions = None
                # NB. in case there are several actions, we reset each
                # 'action._fired' to false only when we're about to call
                # 'action.perform()'.  This means that if
                # 'action.fire()' happens to be called any time before
                # the corresponding perform(), the fire() has no
                # effect---which is the effect we want, because
                # perform() will be called anyway.
                for action in actions:
                    action._fired = False
                    action.perform(ec, frame)

        self.action_dispatcher = action_dispatcher


class ActionFlag(AbstractActionFlag):
    """The normal class for space.actionflag.  The signal module provides
    a different one."""
    _ticker = 0

    def get_ticker(self):
        return self._ticker

    def reset_ticker(self, value):
        self._ticker = value

    def decrement_ticker(self, by):
        value = self._ticker
        if self.has_bytecode_counter:    # this 'if' is constant-folded
            if jit.isconstant(by) and by == 0:
                pass     # normally constant-folded too
            else:
                value -= by
                self._ticker = value
        return value


class AsyncAction(object):
    """Abstract base class for actions that must be performed
    asynchronously with regular bytecode execution, but that still need
    to occur between two opcodes, not at a completely random time.
    """
    _fired = False

    def __init__(self, space):
        self.space = space

    def fire(self):
        """Request for the action to be run before the next opcode.
        The action must have been registered at space initalization time."""
        self.space.actionflag.fire(self)

    def perform(self, executioncontext, frame):
        """To be overridden."""


class PeriodicAsyncAction(AsyncAction):
    """Abstract base class for actions that occur automatically
    every TICK_COUNTER_STEP bytecodes.
    """
