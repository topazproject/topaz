from __future__ import absolute_import

import os
import sys

from pypy.rlib.objectmodel import specialize
from pypy.rlib.streamio import open_file_as_stream

from rupypy.error import RubyError, format_traceback
from rupypy.objects.objectobject import W_Object
from rupypy.objspace import ObjectSpace


@specialize.memo()
def getspace():
    return ObjectSpace()


def entry_point(argv):
    space = getspace()

    verbose = False
    path = None
    argv_w = []
    idx = 1
    while idx < len(argv):
        arg = argv[idx]
        idx += 1
        if arg == "-v":
            verbose = True
        else:
            path = arg
            while idx < len(argv):
                arg = argv[idx]
                idx += 1
                argv_w.append(space.newstr_fromstr(arg))
    space.set_const(space.getclassfor(W_Object), "ARGV", space.newarray(argv_w))

    if verbose:
        system, _, _, _, cpu = os.uname()
        os.write(1, "rupypy (ruby-1.9.3p125) [%s-%s]\n" % (cpu, system.lower()))
    if path is not None:
        f = open_file_as_stream(path)
        try:
            source = f.readall()
        finally:
            f.close()

        try:
            space.execute(source, filepath=path)
        except RubyError as e:
            lines = format_traceback(space, e.w_value)
            for line in lines:
                os.write(2, line)
            return 1
    return 0

if __name__ == "__main__":
    entry_point(sys.argv)
