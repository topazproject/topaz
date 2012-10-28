import sys

from rupypy.main import entry_point


try:
    entry_point(sys.argv)
except:
    import pdb
    pdb.post_mortem(sys.exc_info()[2])
