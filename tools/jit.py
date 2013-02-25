#!/usr/bin/env python

source = """
a = 0
(1..10000).each do |i|
  a = i + 1
end
"""

import os
from rpython import conftest
from rpython.jit.metainterp.test.test_ajit import LLJitMixin
from rpython.rlib.streamio import open_file_as_stream, fdopen_as_stream

from topaz.objspace import ObjectSpace
from topaz.error import RubyError, print_traceback


class o:
    view = False
    viewloops = True
conftest.option = o


space = ObjectSpace()
space.setup(os.path.join(os.path.dirname(__file__), os.path.pardir, "bin", "topaz"))


class TestLLtype(LLJitMixin):
    def test_miniloop(self):
        bc = space.compile(source, filepath=__file__, initial_lineno=1)
        frame = space.create_frame(bc)
        def interp_w():
            with space.getexecutioncontext().visit_frame(frame):
                return space.execute_frame(frame, bc)
        self.meta_interp(interp_w, [], listcomp=True, listops=True, backendopt=True)

if __name__ == "__main__":
    try:
        TestLLtype().test_miniloop()
    except RubyError as e:
        print_traceback(space, e.w_value, __file__)
