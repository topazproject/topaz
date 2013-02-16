import sys
import os
import platform

POSIX = os.name == "posix"
WINDOWS = os.name == "nt"
LINUX = "linux" in sys.platform
IS64BIT = "64bit" in platform.architecture()[0]
CYGWIN = "cygwin" == sys.platform
