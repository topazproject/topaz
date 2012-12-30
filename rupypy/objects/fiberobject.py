from pypy.rlib import jit
from pypy.rlib.rstacklet import StackletThread

from rupypy.module import ClassDef
from rupypy.objects.objectobject import W_Object


class W_FiberObject(W_Object):
    classdef = ClassDef("Fiber", W_Object.classdef, filepath=__file__)

    def __init__(self, space, klass):
        W_Object.__init__(self, space, klass)
        self.w_block = None

    @classdef.singleton_method("allocate")
    def singleton_method_allocate(self, space):
        return W_FiberObject(space, self)

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
            block.bytecode, w_self=block.w_self,
            lexical_scope=block.lexical_scope, block=block.block,
            parent_interp=block.parent_interp,
            regexp_match_cell=block.regexp_match_cell,
        )
        global_state.origin = self
        global_state.space = space
        h = sthread.new(new_stacklet_callback)
        post_switch(sthread, h)

    @classdef.method("resume")
    def method_resume(self, space, args_w):
        pass


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
        self.space = None
# This makes me sad.
global_state = GlobalState()


def new_stacklet_callback(h, arg):
    self = global_state.origin
    space = global_state.space
    self.h = h
    global_state.clear()

    with self.sthread.ec.visit_frame(self.bottomframe):
        global_state.w_result = space.execute_frame(self.bottomframe, self.w_block.bytecode)

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
    w_result = global_state.w_result
    global_state.w_result = None
    return w_result


def workaround_disable_jit(sthread):
    # TODO: fill this in.
    pass
