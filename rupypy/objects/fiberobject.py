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
            sthread = ec.fiber_thread = StackletThread()
        workaround_disable_jit(sthread)
        self.sthread = sthread
        self.bottomframe = space.create_frame(
            block.bytecode, w_self=block.w_self,
            lexical_scope=block.lexical_scope, block=block.block,
            parent_interp=block.parent_interp,
            regexp_match_cell=block.regexp_match_cell,
        )
        h = sthread.new(new_stacklet_callback)
        post_switch(sthread, h)

    @classdef.method("resume")
    def method_resume(self, space, args_w):
        pass
