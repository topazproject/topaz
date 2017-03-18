import weakref

from rpython.rlib import rshrinklist, rthread
from rpython.rlib import rgil
from rpython.rlib.objectmodel import not_rpython, we_are_translated

from topaz.executioncontext import ExecutionContext, PeriodicAsyncAction


class ThreadLocals(object):
    # Inspired by Pypy's GILThreadLocals/OSThreadLocals
    gil_ready = False
    _immutable_fields_ = ['gil_ready?']

    @not_rpython
    def __init__(self, space):
        self.space = space
        self._valuedict = {}
        self._cleanup_()
        self.raw_thread_local = rthread.ThreadLocalReference(
            ExecutionContext, loop_invariant=True)
        # add the GIL-releasing callback as an action on the space
        space.actionflag.register_periodic_action(GILReleaseAction(space),
                                                  use_bytecode_counter=True)

    def can_optimize_with_weaklist(self):
        config = self.space.config
        return (config.translation.rweakref and
                rthread.ThreadLocalReference.automatic_keepalive(config))

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
        if not self.can_optimize_with_weaklist():
            self._set_ec(ec)
            return True

        # If can_optimize_with_weaklist(), then 'rthread' keeps the
        # thread-local values alive until the end of the thread.  Use
        # AutoFreeECWrapper as an object with a __del__; when this
        # __del__ is called, it means the thread was really finished.
        # In this case we don't want leave_thread() to be called
        # explicitly, so we return False.
        if self._weaklist is None:
            self._weaklist = ListECWrappers()
        self._weaklist.append(weakref.ref(AutoFreeECWrapper(ec)))
        self._set_ec(ec, register_in_valuedict=False)
        return False

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
                thread_is_stopping(ec)
            finally:
                self.raw_thread_local.set(None)
                ident = rthread.get_ident()
                try:
                    del self._valuedict[ident]
                except KeyError:
                    pass

    def setup_threads(self, space):
        """Enable threads in the object space, if they haven't already been."""
        if not self.gil_ready:
            # Note: this is a quasi-immutable read by module/pypyjit/interp_jit
            # It must be changed (to True) only if it was really False before
            rgil.allocate()
            self.gil_ready = True
            result = True
        else:
            result = False      # already set up
        return result

    def threads_initialized(self):
        return self.gil_ready


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


class AutoFreeECWrapper(object):
    deleted = False

    def __init__(self, ec):
        # this makes a loop between 'self' and 'ec'.  It should not prevent
        # the __del__ method here from being called.
        self.ec = ec
        ec._threadlocals_auto_free = self
        self.ident = rthread.get_ident()

    def __del__(self):
        # this is always called in another thread: the thread
        # referenced by 'self.ec' has finished at that point, and
        # we're just after the GC which finds no more references to
        # 'ec' (and thus to 'self').
        self.deleted = True
        thread_is_stopping(self.ec)


class ListECWrappers(rshrinklist.AbstractShrinkList):
    def must_keep(self, wref):
        return wref() is not None


class GILReleaseAction(PeriodicAsyncAction):
    """An action called every TICK_COUNTER_STEP bytecodes.  It releases
    the GIL to give some other thread a chance to run.
    """

    def perform(self, executioncontext, frame):
        rgil.yield_thread()
