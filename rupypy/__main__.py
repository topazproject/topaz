import sys

import py
py.log.setconsumer("platform", None)

from rupypy.main import entry_point


entry_point(sys.argv)
