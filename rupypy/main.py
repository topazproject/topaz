"""rupypy"""

from pypy.rlib.streamio import open_file_as_stream

from rupypy.objspace import ObjectSpace


def entry_point(argv):
    if len(argv) != 2:
        print __doc__
        return 1

    f = open_file_as_stream(argv[1])
    try:
        source = f.readall()
    finally:
        f.close()

    space = ObjectSpace()
    space.execute(source)
    return 0