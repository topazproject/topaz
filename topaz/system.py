import sys
import os
import platform

IS_POSIX = os.name == "posix"
IS_WINDOWS = os.name == "nt"
IS_LINUX = "linux" in sys.platform
IS_64BIT = "64bit" in platform.architecture()[0]
IS_CYGWIN = "cygwin" == sys.platform
