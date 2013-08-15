import copy

from rpython.rlib import jit
from rpython.rlib.rstacklet import StackletThread

from topaz.interpreter import RaiseReturn, RaiseBreak
from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object


class State(object):
    def __init__(self, space):
        self.current = None

    def get_current(self, space):
        return self.current or space.getexecutioncontext().getmainfiber(space)


class W_FiberObject(W_Object):
    """
    Fibers have a number of possible states:

    * Has not yet begun execution: self.sthread is None
    * Currently execution: self.sthread is not None and self is State.get_current()
    * Suspended execution: self.sthread is not None and self.parent_fiber is None
    * Suspended execution in the stack of fibers: self.sthread is not None and (self.parent_fiber is None or self is space.w_main_fiber)
    * Dead: self.sthread is not None and self.sthread.is_empty_handle(self.h)
    """
    classdef = ClassDef("Fiber", W_Object.classdef)

    def __init__(self, space, klass=None):
        W_Object.__init__(self, space, klass)
        self.w_block = None
        self.sthread = None
        self.parent_fiber = None

    def __deepcopy__(self, memo):
        obj = super(W_FiberObject, self).__deepcopy__(memo)
        obj.w_block = copy.deepcopy(self.w_block, memo)
        obj.sthread = copy.deepcopy(self.sthread, memo)
        obj.parent_fiber = copy.deepcopy(self.parent_fiber, memo)
        return obj

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
        parent_fiber = current.parent_fiber
        if parent_fiber is None:
            raise space.error(space.w_FiberError, "can't yield from root fiber")
        space.fromcache(State).current = parent_fiber

        topframeref = space.getexecutioncontext().topframeref
        current.bottomframe.backref = jit.vref_None
        if len(args_w) == 0:
            global_state.w_result = space.w_nil
        elif len(args_w) == 1:
            global_state.w_result = args_w[0]
        else:
            global_state.w_result = space.newarray(args_w)
        parent_fiber.h = space.getexecutioncontext().fiber_thread.switch(parent_fiber.h)
        assert space.fromcache(State).current is current
        current.bottomframe.backref = space.getexecutioncontext().topframeref
        space.getexecutioncontext().topframeref = topframeref

        return get_result()

    @classdef.method("initialize")
    @jit.unroll_safe
    def method_initialize(self, space, block):
        if block is None:
            raise space.error(space.w_ArgumentError)
        self.w_block = block
        self.bottomframe = space.create_frame(
            self.w_block.bytecode, w_self=self.w_block.w_self,
            lexical_scope=self.w_block.lexical_scope, block=self.w_block.block,
            parent_interp=self.w_block.parent_interp,
            top_parent_interp=self.w_block.top_parent_interp,
            regexp_match_cell=self.w_block.regexp_match_cell,
        )
        for idx, cell in enumerate(self.w_block.cells):
            self.bottomframe.cells[len(self.w_block.bytecode.cellvars) + idx] = cell

    @classdef.method("resume")
    def method_resume(self, space, args_w):
        if self.parent_fiber is not None:
            raise space.error(space.w_FiberError, "double resume")
        if self.sthread is not None and self.sthread.is_empty_handle(self.h):
            raise space.error(space.w_FiberError, "dead fiber called")

        self.parent_fiber = space.fromcache(State).get_current(space)
        try:
            global_state.space = space
            global_state.space.fromcache(State).current = self
            topframeref = space.getexecutioncontext().topframeref
            if self.sthread is None:
                self.bottomframe.handle_block_args(space, self.w_block.bytecode, args_w, self.w_block)
                sthread = self.get_sthread(space, space.getexecutioncontext())
                self.sthread = sthread
                self.h = sthread.new(new_stacklet_callback)
            else:
                if len(args_w) == 1:
                    global_state.w_result = args_w[0]
                else:
                    global_state.w_result = space.newarray(args_w)
                self.h = self.sthread.switch(self.h)
            assert space.fromcache(State).current is self.parent_fiber
            space.getexecutioncontext().topframeref = topframeref
            return get_result()
        finally:
            self.parent_fiber = None


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
        self.w_result = None
        self.propagate_exception = None
        self.space = None
# This makes me sad.
global_state = GlobalState()


def new_stacklet_callback(h, arg):
    space = global_state.space
    self = space.fromcache(State).current
    origin = self.parent_fiber
    origin.h = h
    global_state.clear()

    with self.sthread.ec.visit_frame(self.bottomframe):
        try:
            try:
                global_state.w_result = space.execute_frame(self.bottomframe, self.w_block.bytecode)
            except RaiseReturn:
                raise space.error(space.w_LocalJumpError, "unexpected return")
            except RaiseBreak:
                raise space.error(space.w_LocalJumpError, "break from proc-closure")
        except Exception as e:
            global_state.propagate_exception = e

    space.fromcache(State).current = self.parent_fiber
    global_state.space = space
    return origin.h


def get_result():
    if global_state.propagate_exception:
        e = global_state.propagate_exception
        global_state.propagate_exception = None
        raise e
    else:
        w_result = global_state.w_result
        global_state.w_result = None
        return w_result
