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
    if len(argv) != 2:
        print "Usage: %s <program>" % argv[0]
        print "Arguments: %s" % argv
        return 1

    f = open_file_as_stream(argv[1])
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
