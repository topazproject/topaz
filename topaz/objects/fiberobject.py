import copy

from rpython.rlib import jit
from rpython.rlib.rstacklet import StackletThread

from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object


class State(object):
    def __init__(self, space):
        self.current = None

    def get_current(self, space):
        return self.current or space.getexecutioncontext()


class W_FiberObject(W_Object):
    """
    Fibers have a number of possible states:

    * Has not yet begun execution: self.sthread is None
    * Currently execution: self.sthread is not None and self is State.get_current()
    * Suspended execution: self.sthread is not None and self.parent_fiber is None
    * Suspended execution in the stack of fibers: self.sthread is not None and (self.parent_fiber is None or self is space.w_main_fiber)
    * Dead: self.sthread is not None and self.sthread.is_empty_handle(self.h)
    """
    classdef = ClassDef("Fiber", W_Object.classdef, filepath=__file__)

    def __init__(self, space, klass=None):
        W_Object.__init__(self, space, klass)
        self.w_block = None
        self.sthread = None
        self.parent_fiber = None

    @staticmethod
    def build_main_fiber(space, ec):
        w_fiber = W_FiberObject(space)
        w_fiber.sthread = W_FiberObject.get_sthread(space, ec)
        return w_fiber

    @staticmethod
    def get_sthread(space, ec):
        sthread = ec.fiber_thread
        if not sthread:
            sthread = ec.fiber_thread = SThread(space.config, ec)
        return sthread

    @classdef.singleton_method("allocate")
    def singleton_method_allocate(self, space):
        return W_FiberObject(space, self)

    @classdef.singleton_method("yield")
    def singleton_method_yield(self, space, args_w):
        current = space.fromcache(State).get_current(space)
        space.getexecutioncontext().fiber_thread.switch(current.h)
        return post_switch(space.getexecutioncontext().fiber_thread, current.h)

    @classdef.method("initialize")
    def method_initialize(self, space, block):
        if block is None:
            raise space.error(space.w_ArgumentError)
        self.w_block = block
        self.bottomframe = space.create_frame(
            self.w_block.bytecode, w_self=self.w_block.w_self,
            lexical_scope=self.w_block.lexical_scope, block=self.w_block.block,
            parent_interp=self.w_block.parent_interp,
            regexp_match_cell=self.w_block.regexp_match_cell,
        )
        for idx, cell in enumerate(self.w_block.cells):
            self.bottomframe.cells[len(self.w_block.bytecode.cellvars) + idx] = cell

    @classdef.method("resume")
    def method_resume(self, space, args_w):
        if self.parent_fiber is not None:
            raise space.error(space.w_FiberError, "double resume")
        if self.sthread is None:
            sthread = self.get_sthread(space, space.getexecutioncontext())
            self.sthread = sthread
            self.parent_fiber = space.fromcache(State).get_current(space)
            try:
                global_state.origin = self
                global_state.space = space
                h = sthread.new(new_stacklet_callback)
                return post_switch(sthread, h)
            finally:
                self.parent_fiber = None
        else:
            XXX


class SThread(StackletThread):
    def __init__(self, config, ec):
        StackletThread.__init__(self, config)
        self.config = config
        self.ec = ec

    def __deepcopy__(self, memo):
        return SThread(self.config, copy.deepcopy(self.ec, memo))


class GlobalState(object):
    def __init__(self):
        self.clear()

    def clear(self):
        self.origin = None
        self.destination = None
        self.w_result = None
        self.propagate_exception = None
        self.space = None
# This makes me sad.
global_state = GlobalState()


def new_stacklet_callback(h, arg):
    self = global_state.origin
    space = global_state.space
    self.h = h
    global_state.clear()
    space.fromcache(State).current = self

    with self.sthread.ec.visit_frame(self.bottomframe):
        try:
            global_state.w_result = space.execute_frame(self.bottomframe, self.w_block.bytecode)
        except Exception as e:
            global_state.propagate_exception = e

    self.sthread.ec.topframeref = jit.vref_None
    global_state.origin = self
    global_state.destination = self
    return self.h


def post_switch(sthread, h):
    origin = global_state.origin
    self = global_state.destination
    global_state.origin = None
    global_state.destination = None
    self.h, origin.h = origin.h, h

    current = sthread.ec.topframeref
    sthread.ec.topframeref = self.bottomframe.backref
    self.bottomframe.backref = origin.bottomframe.backref
    origin.bottomframe.backref = current

    return get_result()


def get_result():
    if global_state.propagate_exception:
        e = global_state.propagate_exception
        global_state.propagate_exception = None
        raise e
    else:
        w_result = global_state.w_result
        global_state.w_result = None
        return w_result
