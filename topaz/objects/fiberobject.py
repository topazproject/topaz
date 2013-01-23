from rpython.rlib import jit
from rpython.rlib.rstacklet import StackletThread

from topaz.module import ClassDef
from topaz.objects.objectobject import W_Object


class State(object):
    def __init__(self, space):
        self.current = None

    def get_current(self):
        return self.current


class W_FiberObject(W_Object):
    classdef = ClassDef("Fiber", W_Object.classdef, filepath=__file__)

    def __init__(self, space, klass):
        W_Object.__init__(self, space, klass)
        self.w_block = None

    @classdef.singleton_method("allocate")
    def singleton_method_allocate(self, space):
        return W_FiberObject(space, self)

    @classdef.singleton_method("yield")
    def singleton_method_yield(self, space, args_w):
        current = space.fromcache(State).get_current()
        space.getexecutioncontext().fiber_thread.switch(current.h)
        return post_switch(space.getexecutioncontext().fiber_thread, current.h)

    @classdef.method("initialize")
    def method_initialize(self, space, block):
        if block is None:
            raise space.error(space.w_ArgumentError)
        self.w_block = block
        ec = space.getexecutioncontext()
        sthread = ec.fiber_thread
        if not sthread:
            sthread = ec.fiber_thread = SThread(space.config, space.getexecutioncontext())
        workaround_disable_jit(sthread)
        self.sthread = sthread
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
        ec = space.getexecutioncontext()
        sthread = ec.fiber_thread
        global_state.origin = self
        global_state.space = space
        workaround_disable_jit(sthread)
        h = sthread.new(new_stacklet_callback)
        return post_switch(sthread, h)


class SThread(StackletThread):
    def __init__(self, config, ec):
        StackletThread.__init__(self, config)
        self.ec = ec


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


def workaround_disable_jit(sthread):
    # TODO: fill this in.
    pass
