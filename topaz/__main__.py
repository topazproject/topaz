import sys

import py
py.log.setconsumer("platform", None)

from topaz.main import entry_point


sys.exit(entry_point(sys.argv))
