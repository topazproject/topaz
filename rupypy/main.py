"""rupypy"""

import sys

from pypy.rlib.objectmodel import specialize
from pypy.rlib.streamio import open_file_as_stream

from rupypy.objspace import ObjectSpace


@specialize.memo()
def getspace():
    return ObjectSpace()

def entry_point(argv):
    if len(argv) != 2:
        print __doc__
        return 1

    f = open_file_as_stream(argv[1])
    try:
        source = f.readall()
    finally:
        f.close()

    space = getspace()
    space.execute(source)
    return 0

if __name__ == "__main__":
    entry_point(sys.argv)
