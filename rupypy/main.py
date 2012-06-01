from __future__ import absolute_import

import os
import sys

from pypy.rlib.objectmodel import specialize
from pypy.rlib.streamio import open_file_as_stream

from rupypy.error import RubyError
from rupypy.executioncontext import ExecutionContext
from rupypy.objspace import ObjectSpace
from rupypy.utils import format_traceback


@specialize.memo()
def getspace():
    return ObjectSpace()


def entry_point(argv):
    verbose = False
    path = None
    idx = 1
    while idx < len(argv):
        arg = argv[idx]
        idx += 1
        if arg == "-v":
            verbose = True
        else:
            path = arg
            break

    if verbose:
        system, _, _, _, cpu = os.uname()
        os.write(1, "rupypy (ruby-1.9.3p125) [%s-%s]\n" % (cpu, system.lower()))
    if path is not None:
        f = open_file_as_stream(path)
        try:
            source = f.readall()
        finally:
            f.close()

        space = getspace()
        ec = ExecutionContext(space)
        try:
            space.execute(ec, source, filepath=argv[1])
        except RubyError as e:
            lines = format_traceback(space, e.w_value)
            for line in lines:
                os.write(2, line)
            return 1
    return 0

if __name__ == "__main__":
    entry_point(sys.argv)
